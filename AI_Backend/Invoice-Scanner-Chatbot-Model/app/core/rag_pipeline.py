import os
import json
import tempfile
import base64
from io import BytesIO
from typing import TypedDict, Optional, List, Any
import pandas as pd
import matplotlib.pyplot as plt
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.document_loaders import CSVLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END


# Define the State for LangGraph
class State(TypedDict):
    question: str
    documents: Optional[List[Document]]
    answer: Optional[str]
    table: Optional[pd.DataFrame]
    decision: Optional[str]  # For relevance grading
    table_decision: Optional[str]  # For table routing
    graph_decision: Optional[str]  # For graph routing
    graph_fig: Optional[Any]  # For matplotlib figure


class InvoiceRAGPipeline:
    """Main RAG pipeline for invoice analysis"""
    
    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            groq_api_key= groq_api_key,
            temperature=0, 
            model="openai/gpt-oss-20b"  # Using a valid Groq model
        )
        self.embeddings = FastEmbedEmbeddings()
    
    def load_documents_from_files(self, files: List[tuple]) -> List[Document]:
        """
        Load documents from uploaded files
        Args:
            files: List of tuples (filename, file_content_bytes)
        Returns:
            List of Document objects
        """
        docs = []
        for filename, file_bytes in files:
            if filename.endswith('.json'):
                # Load JSON and convert to structured text for embedding
                try:
                    data = json.loads(file_bytes.decode('utf-8'))
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        # If it's an array, process each item
                        for i, item in enumerate(data):
                            if isinstance(item, dict):
                                text = json.dumps(item, indent=2)
                                docs.append(Document(
                                    page_content=text, 
                                    metadata={"source": filename, "item_index": i}
                                ))
                    elif isinstance(data, dict):
                        # If it's a single object, use it directly
                        text = json.dumps(data, indent=2)
                        docs.append(Document(page_content=text, metadata={"source": filename}))
                    else:
                        # For primitive types, convert to string
                        text = str(data)
                        docs.append(Document(page_content=text, metadata={"source": filename}))
                        
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON file {filename}: {str(e)}")
                except Exception as e:
                    raise ValueError(f"Error processing JSON file {filename}: {str(e)}")
            
            elif filename.endswith('.csv'):
                # Save uploaded file to a temp path
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as temp_file:
                    temp_file.write(file_bytes)
                    temp_path = temp_file.name
                
                try:
                    loader = CSVLoader(file_path=temp_path, source_column=None)
                    csv_docs = loader.load()
                    # Concatenate all row contents into one document for the invoice
                    text = "\n".join(doc.page_content for doc in csv_docs)
                    docs.append(Document(page_content=text, metadata={"source": filename}))
                finally:
                    os.remove(temp_path)  # Clean up temp file
        
        return docs
    
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """Create FAISS vector store from documents"""
        if not documents:
            raise ValueError("No documents provided to create vector store")
        
        vector_store = FAISS.from_documents(documents, self.embeddings)
        return vector_store
    
    def create_agent(self, retriever) -> Any:
        """Create the LangGraph agent with all nodes and edges"""
        
        # Define prompts
        grade_prompt = ChatPromptTemplate.from_template(
            """Analyze the following documents and determine if they are relevant to the question.
            Answer only with 'yes' or 'no'.

            Documents:
            {docs}

            Question: {question}"""
        )
        generate_prompt = ChatPromptTemplate.from_template(
            """Based on the following documents, provide a concise answer to the question.
            and Please provide the response in plain text with clear spacing, no tables or Markdown, and a conversational tone
            Documents:
            {docs}

            Question: {question}"""
        )
        route_prompt = ChatPromptTemplate.from_template(
            """Does the following question and answer require presenting the information as a table?
            For example, if it involves listing multiple items, line items, or structured data points.
            Answer only with 'yes' or 'no'.

            Question: {question}
            Answer: {answer}"""
        )
        table_prompt = ChatPromptTemplate.from_template(
            """Convert the following answer text into a structured JSON array of objects,
            where each object represents a row in a table. Infer appropriate column keys from the data.
            Output only valid JSON.

            Answer: {answer}"""
        )
        route_graph_prompt = ChatPromptTemplate.from_template(
            """Does the following question require a graph visualization such as a chart or plot?
            Answer only with 'yes' or 'no'.

            Question: {question}
            Answer: {answer}"""
        )
        graph_prompt = ChatPromptTemplate.from_template(
            """Based on the question and answer, generate a JSON for graph visualization.
            Supported types: bar, line, pie.
            For bar: {{"type": "bar", "title": str, "x_label": str, "y_label": str, "categories": [str], "values": [num]}}
            For line: {{"type": "line", "title": str, "x_label": str, "y_label": str, "x": [num/str], "y": [num]}}
            For pie: {{"type": "pie", "title": str, "labels": [str], "values": [num]}}
            Output only valid JSON.

            Question: {question}
            Answer: {answer}"""
        )

        # Node: Retrieve documents
        def retrieve(state: State) -> State:
            question = state["question"]
            docs = retriever.invoke(question)
            return {"documents": docs}

        # Node: Grade documents for relevance
        def grade_documents(state: State) -> State:
            question = state["question"]
            docs = state["documents"]
            docs_str = "\n\n".join(doc.page_content for doc in docs)
            chain = grade_prompt | self.llm | StrOutputParser()
            response = chain.invoke({"docs": docs_str, "question": question})
            decision = "generate" if "yes" in response.lower() else "end"
            return {"decision": decision}

        # Node: Generate answer
        def generate(state: State) -> State:
            question = state["question"]
            docs = state["documents"]
            docs_str = "\n\n".join(doc.page_content for doc in docs)
            chain = generate_prompt | self.llm | StrOutputParser()
            answer = chain.invoke({"docs": docs_str, "question": question})
            return {"answer": answer}

        # Node: Route to table or end
        def route_to_table(state: State) -> State:
            question = state["question"]
            answer = state["answer"]
            chain = route_prompt | self.llm | StrOutputParser()
            response = chain.invoke({"question": question, "answer": answer})
            table_decision = "format_table" if "yes" in response.lower() else "route_to_graph"
            return {"table_decision": table_decision}

        # Node: Format table
        def format_table(state: State) -> State:
            answer = state["answer"]
            chain = table_prompt | self.llm
            response = chain.invoke({"answer": answer})
            try:
                json_data = json.loads(response.content)
                if isinstance(json_data, list) and all(isinstance(item, dict) for item in json_data):
                    df = pd.DataFrame(json_data)
                    return {"table": df}
                else:
                    return {"table": None}
            except Exception:
                return {"table": None}

        # Node: Route to graph or end
        def route_to_graph(state: State) -> State:
            question = state["question"]
            answer = state["answer"]
            chain = route_graph_prompt | self.llm | StrOutputParser()
            response = chain.invoke({"question": question, "answer": answer})
            graph_decision = "format_graph" if "yes" in response.lower() else "end"
            return {"graph_decision": graph_decision}

        # Node: Format graph
        def format_graph(state: State) -> State:
            question = state["question"]
            answer = state["answer"]
            chain = graph_prompt | self.llm
            response = chain.invoke({"question": question, "answer": answer})
            try:
                json_data = json.loads(response.content)
                fig, ax = plt.subplots(figsize=(10, 6))
                graph_type = json_data.get("type")
                title = json_data.get("title", "")
                
                if graph_type == "bar":
                    categories = json_data.get("categories", [])
                    values = json_data.get("values", [])
                    ax.bar(categories, values)
                    ax.set_xlabel(json_data.get("x_label", ""))
                    ax.set_ylabel(json_data.get("y_label", ""))
                elif graph_type == "line":
                    x = json_data.get("x", [])
                    y = json_data.get("y", [])
                    ax.plot(x, y)
                    ax.set_xlabel(json_data.get("x_label", ""))
                    ax.set_ylabel(json_data.get("y_label", ""))
                elif graph_type == "pie":
                    labels = json_data.get("labels", [])
                    values = json_data.get("values", [])
                    ax.pie(values, labels=labels, autopct='%1.1f%%')
                
                ax.set_title(title)
                plt.tight_layout()
                return {"graph_fig": fig}
            except Exception:
                return {"graph_fig": None}

        # Assemble the graph
        graph = StateGraph(State)
        graph.add_node("retrieve", retrieve)
        graph.add_node("grade_documents", grade_documents)
        graph.add_node("generate", generate)
        graph.add_node("route_to_table", route_to_table)
        graph.add_node("format_table", format_table)
        graph.add_node("route_to_graph", route_to_graph)
        graph.add_node("format_graph", format_graph)

        # Set entry point
        graph.set_entry_point("retrieve")

        # Edges
        graph.add_edge("retrieve", "grade_documents")
        graph.add_conditional_edges(
            "grade_documents",
            lambda state: state.get("decision", "end"),
            {"generate": "generate", "end": END}
        )
        graph.add_edge("generate", "route_to_table")
        graph.add_conditional_edges(
            "route_to_table",
            lambda state: state.get("table_decision", "route_to_graph"),
            {"format_table": "format_table", "route_to_graph": "route_to_graph"}
        )
        graph.add_edge("format_table", "route_to_graph")
        graph.add_conditional_edges(
            "route_to_graph",
            lambda state: state.get("graph_decision", "end"),
            {"format_graph": "format_graph", "end": END}
        )
        graph.add_edge("format_graph", END)

        # Compile the graph
        agent = graph.compile()
        return agent

    @staticmethod
    def matplotlib_to_base64(fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)  # Clean up memory
        return image_base64
