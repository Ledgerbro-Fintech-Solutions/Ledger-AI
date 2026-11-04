import os
import re
import json
import tempfile
import base64
from io import BytesIO
from typing import TypedDict, Optional, List, Any

# Ensure headless matplotlib for server environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.document_loaders import CSVLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END

from backend.app.core.config import settings
from backend.app.core.logging import logger


def clean_llm_json_text(text: str) -> str:
    """Clean markdown code fences, think tags, and preamble from LLM JSON response."""
    if not text:
        return ""
    # Strip <think>...</think>
    text = re.sub(r'<think>[\s\S]*?</think>', '', text)
    # Strip markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text.strip(), flags=re.MULTILINE)
    text = text.strip()
    return text


def extract_json_object_or_array(text: str) -> Optional[Any]:
    """Robustly parse JSON object or list from text."""
    cleaned = clean_llm_json_text(text)
    # Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try finding outer [ ... ]
    match_arr = re.search(r'\[[\s\S]*\]', cleaned)
    if match_arr:
        try:
            return json.loads(match_arr.group(0))
        except Exception:
            pass

    # Try finding outer { ... }
    match_obj = re.search(r'\{[\s\S]*\}', cleaned)
    if match_obj:
        try:
            return json.loads(match_obj.group(0))
        except Exception:
            pass

    return None


class State(TypedDict):
    question: str
    documents: Optional[List[Document]]
    answer: Optional[str]
    table: Optional[pd.DataFrame]
    decision: Optional[str]
    table_decision: Optional[str]
    graph_decision: Optional[str]
    graph_fig: Optional[Any]


class InvoiceRAGPipeline:
    """RAG pipeline for invoice analysis with LangGraph state machine."""

    def __init__(self, groq_api_key: Optional[str] = None):
        key = groq_api_key or settings.groq_api_key
        self.llm = ChatGroq(
            groq_api_key=key,
            temperature=settings.llm_temperature,
            model=settings.groq_model_chat
        )
        self.embeddings = FastEmbedEmbeddings()

    def load_documents_from_files(self, files: List[tuple]) -> List[Document]:
        """
        Load documents from uploaded files (filename, file_content_bytes).
        Supports JSON, CSV, and text summaries.
        """
        docs = []
        for filename, file_bytes in files:
            name_lower = filename.lower()
            if name_lower.endswith('.json'):
                try:
                    data = json.loads(file_bytes.decode('utf-8'))
                    if isinstance(data, list):
                        for i, item in enumerate(data):
                            text = json.dumps(item, indent=2) if isinstance(item, (dict, list)) else str(item)
                            docs.append(Document(page_content=text, metadata={"source": filename, "index": i}))
                    elif isinstance(data, dict):
                        # If OCRDataResponse shape
                        if "data" in data and isinstance(data["data"], list):
                            for idx, doc_item in enumerate(data["data"]):
                                text = json.dumps(doc_item, indent=2)
                                docs.append(Document(page_content=text, metadata={"source": filename, "doc_idx": idx}))
                        else:
                            text = json.dumps(data, indent=2)
                            docs.append(Document(page_content=text, metadata={"source": filename}))
                    else:
                        docs.append(Document(page_content=str(data), metadata={"source": filename}))
                except Exception as e:
                    logger.error(f"Error parsing JSON {filename}: {str(e)}")
                    raise ValueError(f"Invalid JSON file {filename}: {str(e)}")

            elif name_lower.endswith('.csv'):
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as temp_file:
                    temp_file.write(file_bytes)
                    temp_path = temp_file.name

                try:
                    loader = CSVLoader(file_path=temp_path, source_column=None)
                    csv_docs = loader.load()
                    text = "\n".join(doc.page_content for doc in csv_docs)
                    docs.append(Document(page_content=text, metadata={"source": filename}))
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                try:
                    text = file_bytes.decode('utf-8', errors='ignore')
                    docs.append(Document(page_content=text, metadata={"source": filename}))
                except Exception as e:
                    logger.warning(f"Could not read text from {filename}: {e}")

        return docs

    def create_vector_store(self, documents: List[Document]) -> FAISS:
        if not documents:
            raise ValueError("No documents provided to create vector store")
        return FAISS.from_documents(documents, self.embeddings)

    def create_agent(self, retriever) -> Any:
        grade_prompt = ChatPromptTemplate.from_template(
            """Analyze the following documents and determine if they are relevant to the question.
Answer with 'yes' or 'no'.

Documents:
{docs}

Question: {question}"""
        )

        generate_prompt = ChatPromptTemplate.from_template(
            """Based on the following documents, answer the financial question accurately and concisely.
Provide clear explanation with proper numbers, dates, and amounts.

Documents:
{docs}

Question: {question}"""
        )

        route_prompt = ChatPromptTemplate.from_template(
            """Does the following question and answer require presenting the information as a table?
(For example: listing multiple invoices, line items, breakdown per vendor or category).
Answer only with 'yes' or 'no'.

Question: {question}
Answer: {answer}"""
        )

        table_prompt = ChatPromptTemplate.from_template(
            """Convert the following answer text into a clean JSON array of objects, where each object represents a row in a table.
CRITICAL: Respond with ONLY a valid JSON array [...]. No explanations, no markdown.

Answer: {answer}"""
        )

        route_graph_prompt = ChatPromptTemplate.from_template(
            """Does the following financial question or answer benefit from a chart or graph visualization (e.g. comparison, distribution, trend, totals)?
Answer only with 'yes' or 'no'.

Question: {question}
Answer: {answer}"""
        )

        graph_prompt = ChatPromptTemplate.from_template(
            """Based on the question and answer, generate a JSON object for graph visualization.
Supported types: bar, line, pie.
For bar: {{"type": "bar", "title": "Chart Title", "x_label": "X Axis", "y_label": "Amount ($)", "categories": ["A", "B"], "values": [100, 200]}}
For line: {{"type": "line", "title": "Chart Title", "x_label": "Time", "y_label": "Amount ($)", "x": ["Jan", "Feb"], "y": [100, 200]}}
For pie: {{"type": "pie", "title": "Chart Title", "labels": ["A", "B"], "values": [100, 200]}}

CRITICAL: Output ONLY valid JSON.

Question: {question}
Answer: {answer}"""
        )

        def retrieve(state: State) -> State:
            question = state["question"]
            docs = retriever.invoke(question)
            return {"documents": docs}

        def grade_documents(state: State) -> State:
            question = state["question"]
            docs = state.get("documents", [])
            docs_str = "\n\n".join(doc.page_content for doc in docs)
            chain = grade_prompt | self.llm | StrOutputParser()
            try:
                response = chain.invoke({"docs": docs_str, "question": question})
                decision = "generate" if "yes" in response.lower() else "end"
            except Exception as e:
                logger.error(f"Grading failed: {e}")
                decision = "generate"
            return {"decision": decision}

        def generate(state: State) -> State:
            question = state["question"]
            docs = state.get("documents", [])
            docs_str = "\n\n".join(doc.page_content for doc in docs)
            chain = generate_prompt | self.llm | StrOutputParser()
            try:
                raw_answer = chain.invoke({"docs": docs_str, "question": question})
                answer = re.sub(r'<think>[\s\S]*?</think>', '', raw_answer).strip()
            except Exception as e:
                logger.error(f"Generate answer failed: {e}")
                answer = f"I encountered an issue generating the answer: {str(e)}"
            return {"answer": answer}

        def route_to_table(state: State) -> State:
            question = str(state.get("question", "")).lower()
            answer = state.get("answer", "")
            table_keywords = ["table", "tabular", "rows", "grid", "line items", "itemized"]
            if any(k in question for k in table_keywords):
                return {"table_decision": "format_table"}

            try:
                chain = route_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"question": question, "answer": answer})
                table_decision = "format_table" if "yes" in response.lower() else "route_to_graph"
            except Exception:
                table_decision = "route_to_graph"
            return {"table_decision": table_decision}

        def format_table(state: State) -> State:
            answer = state["answer"]
            try:
                chain = table_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"answer": answer})
                json_data = extract_json_object_or_array(response)
                if isinstance(json_data, list) and all(isinstance(item, dict) for item in json_data):
                    df = pd.DataFrame(json_data)
                    return {"table": df}
            except Exception as e:
                logger.warning(f"Failed to parse table: {e}")
            return {"table": None}

        def route_to_graph(state: State) -> State:
            question = str(state.get("question", "")).lower()
            graph_keywords = ["chart", "graph", "plot", "bar", "pie", "visual", "visualize", "trend", "histogram"]
            if any(k in question for k in graph_keywords):
                return {"graph_decision": "format_graph"}

            return {"graph_decision": "end"}

        def format_graph(state: State) -> State:
            question = state["question"]
            answer = state["answer"]
            try:
                chain = graph_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"question": question, "answer": answer})
                json_data = extract_json_object_or_array(response)
                if isinstance(json_data, dict):
                    fig, ax = plt.subplots(figsize=(8, 4.5))
                    gtype = json_data.get("type", "bar")
                    title = json_data.get("title", "Financial Overview")
                    
                    # Style modern plot
                    ax.set_facecolor('#ffffff')
                    fig.patch.set_facecolor('#ffffff')

                    if gtype == "bar":
                        categories = json_data.get("categories", [])
                        values = [float(v) for v in json_data.get("values", [])]
                        bars = ax.bar(categories, values, color='#155DFC', edgecolor='#E5E7EB', width=0.55)
                        ax.set_xlabel(json_data.get("x_label", ""), fontsize=10, color='#4B5563')
                        ax.set_ylabel(json_data.get("y_label", "Amount ($)"), fontsize=10, color='#4B5563')
                        ax.grid(axis='y', linestyle='--', alpha=0.3)
                        for bar in bars:
                            h = bar.get_height()
                            ax.annotate(f"{h:g}",
                                        xy=(bar.get_x() + bar.get_width() / 2, h),
                                        xytext=(0, 3), textcoords="offset points",
                                        ha='center', va='bottom', fontsize=9)
                    elif gtype == "line":
                        x = json_data.get("x", [])
                        y = [float(v) for v in json_data.get("y", [])]
                        ax.plot(x, y, marker='o', color='#155DFC', linewidth=2)
                        ax.set_xlabel(json_data.get("x_label", ""), fontsize=10, color='#4B5563')
                        ax.set_ylabel(json_data.get("y_label", "Amount ($)"), fontsize=10, color='#4B5563')
                        ax.grid(True, linestyle='--', alpha=0.3)
                    elif gtype == "pie":
                        labels = json_data.get("labels", [])
                        values = [float(v) for v in json_data.get("values", [])]
                        colors = ['#155DFC', '#10B981', '#F59E0B', '#6366F1', '#EC4899', '#8B5CF6']
                        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors[:len(values)], startangle=140)
                    
                    ax.set_title(title, fontsize=12, fontweight='bold', color='#111827', pad=12)
                    plt.tight_layout()
                    return {"graph_fig": fig}
            except Exception as e:
                logger.warning(f"Failed to generate graph: {e}")
            return {"graph_fig": None}

        # Build Graph
        graph = StateGraph(State)
        graph.add_node("retrieve", retrieve)
        graph.add_node("grade_documents", grade_documents)
        graph.add_node("generate", generate)
        graph.add_node("route_to_table", route_to_table)
        graph.add_node("format_table", format_table)
        graph.add_node("route_to_graph", route_to_graph)
        graph.add_node("format_graph", format_graph)

        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "grade_documents")
        graph.add_conditional_edges(
            "grade_documents",
            lambda s: s.get("decision", "end"),
            {"generate": "generate", "end": END}
        )
        graph.add_edge("generate", "route_to_table")
        graph.add_conditional_edges(
            "route_to_table",
            lambda s: s.get("table_decision", "route_to_graph"),
            {"format_table": "format_table", "route_to_graph": "route_to_graph"}
        )
        graph.add_edge("format_table", "route_to_graph")
        graph.add_conditional_edges(
            "route_to_graph",
            lambda s: s.get("graph_decision", "end"),
            {"format_graph": "format_graph", "end": END}
        )
        graph.add_edge("format_graph", END)

        return graph.compile()

    @staticmethod
    def matplotlib_to_base64(fig) -> str:
        """Convert matplotlib figure to base64 PNG image."""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        return img_b64
