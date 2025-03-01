from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import HuggingFaceHub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # Using a slightly larger model for better responses

def clean_html_content(html_content):
    """Clean HTML content from diary entries"""
    if not html_content:
        return ""
    
    # Use BeautifulSoup to extract text from HTML
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {e}")
        return html_content  # Return original if parsing fails

def prepare_documents(entries):
    """Convert diary entries to langchain Document objects with metadata"""
    documents = []
    
    for entry in entries:
        try:
            # Extract clean text content
            content = clean_html_content(entry.get('content', ''))
            title = entry.get('title', 'Untitled Entry')
            
            if not content.strip():
                continue  # Skip empty entries
                
            # Create metadata for better context
            metadata = {
                'title': title,
                'date': entry.get('created_at', datetime.now()).strftime('%Y-%m-%d'),
                'entry_id': str(entry.get('_id', '')),
                'emoji': entry.get('emoji', '📝'),
                'is_bookmarked': entry.get('is_bookmarked', False)
            }
            
            # Create document with metadata
            doc = Document(
                page_content=f"Title: {title}\n\n{content}",
                metadata=metadata
            )
            documents.append(doc)
            
        except Exception as e:
            logger.error(f"Error processing entry {entry.get('_id', 'unknown')}: {e}")
            continue
            
    return documents

def split_documents(documents):
    """Split documents into chunks for better retrieval"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    return text_splitter.split_documents(documents)

def create_retrieval_chain(vectorstore):
    """Create a chain that retrieves and formats context"""
    template = """You are an AI assistant named "Buddy" for a diary app called "Dear Diary".
    You're friendly, empathetic, and designed to help users reflect on their diary entries.
    
    The user has written the following diary entries:
    {context}
    
    Based on these entries, please respond to the following question or comment from the user:
    {question}
    
    Your response should:
    - Be conversational and friendly
    - Reference specific details from their diary entries when relevant
    - Help the user gain insights from their writing
    - Respect the user's emotions and experiences
    - Not exceed 250 words
    - ONLY include your direct response to the user, DO NOT repeat the question or prompt
    """
    
    PROMPT = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    llm = HuggingFaceHub(
        repo_id=LLM_MODEL,
        huggingfacehub_api_token=HUGGINGFACE_API_TOKEN,
        model_kwargs={
            "temperature": 0.7,
            "max_length": 512,
            "do_sample": True
        }
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Create a more explicit chain with proper output parsing
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    def clean_response(response_and_inputs):
        """Remove the prompt and question from the response"""
        response = response_and_inputs["response"]
        question = response_and_inputs["question"]
        context = response_and_inputs["context"]
        
        # 1. Remove exact prompt if it appears at the start
        formatted_prompt = template.format(context=context, question=question)
        if response.startswith(formatted_prompt):
            response = response[len(formatted_prompt):].strip()
        
        # 2. Remove just the question if it appears at the start
        if response.startswith(question):
            response = response[len(question):].strip()
        
        # 3. Clean up other common patterns
        lines = response.split('\n')
        cleaned_lines = []
        question_pattern_started = False
        
        for line in lines:
            # Skip empty lines at the beginning
            if not cleaned_lines and not line.strip():
                continue
                
            # Skip lines that might be question repetitions
            lower_line = line.lower().strip()
            if not cleaned_lines:
                # Check for common question repetition patterns
                if (lower_line.startswith("question:") or 
                    lower_line.startswith("based on") or
                    "you asked" in lower_line or
                    "your question" in lower_line):
                    question_pattern_started = True
                    continue
            
            # If we were in a question pattern but hit a blank line, we might be done with the repetition
            if question_pattern_started and not line.strip():
                question_pattern_started = False
                continue
                
            # Otherwise, include the line
            if not question_pattern_started:
                cleaned_lines.append(line)
        
        cleaned_response = '\n'.join(cleaned_lines).strip()
        return cleaned_response
    
    # Modified chain to pass context and question to the cleaner
    def rag_chain(query):
        context = format_docs(retriever.invoke(query))
        formatted_prompt = PROMPT.format(context=context, question=query)
        response = llm.invoke(formatted_prompt)
        response_str = StrOutputParser().invoke(response)
        return clean_response({
            "response": response_str,
            "question": query,
            "context": context
        })
    
    # Wrap in a compatible interface for the existing code
    class ChainWrapper:
        def __call__(self, inputs):
            query = inputs.get("query", "")
            result = rag_chain(query)
            return {"result": result}
    
    return ChainWrapper()

def generate_response(query, mongo, username):
    """Generate a response based on user's diary entries using RAG"""
    try:
        logger.info(f"Generating response for query: {query}")
        
        # Get recent entries first (within last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        
        entries = list(mongo.db.diaries.find({
            'username': username,
            'is_deleted': {'$ne': True},
            'created_at': {'$gte': six_months_ago}
        }).sort('created_at', -1))
        
        # If not enough entries, get all non-deleted entries
        if len(entries) < 10:
            entries = list(mongo.db.diaries.find({
                'username': username,
                'is_deleted': {'$ne': True}
            }).sort('created_at', -1))
        
        logger.info(f"Found {len(entries)} entries for retrieval")
        
        if not entries:
            return "I don't see any diary entries yet. Start writing, and I'll be able to chat with you about your experiences!"
        
        # Prepare documents from entries
        documents = prepare_documents(entries)
        if not documents:
            return "I couldn't process your diary entries. Please make sure they contain some text content."
        
        # Split documents into chunks
        splits = split_documents(documents)
        logger.info(f"Created {len(splits)} text chunks for retrieval")
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        
        # Create vector store
        vectorstore = FAISS.from_documents(splits, embeddings)
        
        # Create retrieval chain
        qa_chain = create_retrieval_chain(vectorstore)
        
        # Run chain
        result = qa_chain({"query": query})
        answer = result.get("result", "")
        
        if not answer:
            return "I'm thinking about your question based on your diary entries, but I'm having trouble formulating a response. Could you try asking in a different way?"
        
        return answer
        
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        return "I encountered an error while processing your diary entries. Please try again later."
