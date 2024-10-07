import streamlit as st
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.vectorstores import FAISS
import whisper
from moviepy.editor import VideoFileClip

load_dotenv()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
st.title("AI Teaching Assistant")


uploaded_file = st.file_uploader("Upload a lecture video file for which you want to ask answers", type=["mp4", "mkv", "mov", "avi"])

if uploaded_file is not None:
    
    video_path = os.path.join("temp_video.mp4")
    
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    
    video_clip = VideoFileClip(video_path)

    
    audio_clip = video_clip.audio

    
    audio_output = "extracted_audio.mp3"
    audio_clip.write_audiofile(audio_output)

    
    audio_clip.close()
    video_clip.close()
    
    st.success("Audio extracted successfully!")

    
    st.write("Transcribing the audio, please wait...")

    
    model = whisper.load_model("base")  # You can use other models like "small", "medium", or "large"

  
    transcription_result = model.transcribe(audio_output)


    transcription = transcription_result['text']

  
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_text(transcription)

   
    st.write("Generating embeddings for the transcription...")
    embeddings = OpenAIEmbeddings()
    doc_embeddings = embeddings.embed_documents(docs)

   
    vector_store = FAISS.from_texts(docs, embeddings)


    groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-8b-instant")

    prompt_template = ChatPromptTemplate.from_template("""
    Answer the following question based on the context provided. If the context doesn't contain the answer, say you don't know.
    Context: {context}
    Question: {input}
    """)


    document_chain = create_stuff_documents_chain(llm, prompt_template)

    retriever = vector_store.as_retriever()


    retrieval_chain = create_retrieval_chain(retriever, document_chain)

   
    user_query = st.text_input("Ask a question about the lecture")

    if user_query:
       
        st.write("Processing your query, please wait...")
        response = retrieval_chain.invoke({"input": user_query})
        st.write("**Answer**")
        st.write(response['answer'])

  
    os.remove(video_path)
    os.remove(audio_output)