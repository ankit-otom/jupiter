import logging
import os
import nest_asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI 
from llama_parse import LlamaParse
from typing import List
from io import BytesIO
# from docling.models.tesseract_ocr_cli_model import TesseractCliOcrOptions
# from docling.models.tesseract_ocr_model import TesseractOcrOptions

# os.environ['TESSDATA_PREFIX'] = '/usr/local/bin/tesseract'


# Load environment variables
load_dotenv()
nest_asyncio.apply()
# os.environ["LLAMA_CLOUD_API_KEY"] = "your_api_key_here"

# ocr_options = TesseractOcrOptions()

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"), 
        logging.StreamHandler()         
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI and other components
app = FastAPI()
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options, backend=DoclingParseV2DocumentBackend)  # switch to beta PDF backend
        }
)

llm = ChatOpenAI(
    model="gpt-4o",
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

@app.get("/hi")
async def hi():
    return JSONResponse(content={"results": "hi"})

# Initialize the LlamaParse parser
parser = LlamaParse(result_type="markdown")  # Use "text" for plain text output

@app.post("/upload/llama")
async def upload_files(files: List[UploadFile] = File(...)):
    # Initialize a list to store the parsed results
    results = []

    # Process each uploaded file
    for file in files:
        # Read the file content
        logger.info('reading first file');
        content = await file.read()
        
        file_buffer = BytesIO(content)
        extra_info = {"file_name": file.filename}

        # Parse the content using LlamaParse
        document = parser.load_data(file_buffer, extra_info=extra_info)
        logger.info(document)

        # Append the parsed document to the results list
        results.append({
            "filename": file.filename,
            "parsed_content": document[0].text  # Assuming the document is a list with one item
        })

    # Return the parsed results as a JSON response
    return JSONResponse(content={"results": results})
    
    

@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    logger.info("Received file upload request.")
    results = []
    
    for file in files:
        logger.info(f"Processing file: {file.filename}")
        temp_file_path = f"/tmp/{file.filename}"
        try:
            # Save the file temporarily
            with open(temp_file_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)
            logger.info(f"Saved file to temporary location: {temp_file_path}")
            
            # Process the file using enhanced Docling configuration
            result = converter.convert(temp_file_path)
            
            # Add debugging information
            # logger.debug(f"OCR Settings used: {ocr_options.config_params}")
            logger.debug(f"Pipeline options used: {pipeline_options}")
            
            document_token = result.document.export_to_markdown()
            logger.info(f"Successfully converted {file.filename} to Markdown.")
            
            # Additional logging for debugging
            if '<!------ image ----->' in document_token:
                logger.warning("Image placeholder found in output - OCR might have failed")
            
            results.append({
                "filename": file.filename,
                "content": document_token,
                "ocr_status": "OCR completed" if document_token else "OCR failed"
            })
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Deleted temporary file: {temp_file_path}")
    
    logger.info("File upload request processing complete.")
    return JSONResponse(content={"results": results})

# @app.post("/upload/")
# async def upload_files(files: list[UploadFile] = File(...)):
#     logger.info("Received file upload request.")
#     results = []
    
#     for file in files:
#         logger.info(f"Processing file: {file.filename}")
#         temp_file_path = f"/tmp/{file.filename}"
#         try:
#             # Save the file temporarily
#             with open(temp_file_path, "wb") as temp_file:
#                 content = await file.read()
#                 temp_file.write(content)
#             logger.info(f"Saved file to temporary location: {temp_file_path}")
            
#             # Process the file using Docling
#             result = converter.convert(temp_file_path)
#             document_token = result.document.export_to_markdown()
#             logger.info(f"Successfully converted {file.filename} to Markdown.")
#             logger.info(f"markdown_content {document_token}")

#             messages = [
#                 {
#                     "role": "user", 
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": f"I am giving you 2023 financial statement including p&l and balance sheet, will you be able to show me the carried forward financial statements for 2024 for the purpose of T2 corporate tax for a Canadian Ontario based corporation, year ending August 31, 2024 in accrued accounting method?"
#                             +"data:\n\n{document_token} along with the actual amount. Can you give me the answer in markdown format?",
#                         }
#                     ]
#                 }
#             ]

#             # ai_msg = llm.invoke(messages)

#             # print(ai_msg.content)

#             # results.append({
#             #     "filename": file.filename,
#             #     "analysis": ai_msg.content  
#             # })
            
#         except Exception as e:
#             logger.error(f"Error processing file {file.filename}: {str(e)}")
#             results.append({
#                 "filename": file.filename,
#                 "error": str(e)
#             })
#         finally:
#             if os.path.exists(temp_file_path):
#                 os.remove(temp_file_path)
#                 logger.info(f"Deleted temporary file: {temp_file_path}")
    
#     logger.info("File upload request processing complete.")
#     return JSONResponse(content={"results": results})


# @app.post("/upload/")
# async def upload_files(files: list[UploadFile] = File(...)):
#     llm = get_llm()
#     logger.info("Received file upload request.")
#     results = []
    
#     for file in files:
#         logger.info(f"Processing file: {file.filename}")
#         temp_file_path = f"/tmp/{file.filename}"
#         try:
#             # Save the file temporarily
#             with open(temp_file_path, "wb") as temp_file:
#                 content = await file.read()
#                 temp_file.write(content)
#             logger.info(f"Saved file to temporary location: {temp_file_path}")
            
#             # Process the file using Docling
#             result = converter.convert(temp_file_path)
#             markdown_content = result.document.export_to_markdown()
#             logger.info(f"Successfully converted {file.filename} to Markdown.")
#             logger.info(f"markdown_content {markdown_content}")
            
#             # Define a LangChain prompt and execute it
#             prompt = PromptTemplate(
#                 input_variables=["content"],
#                 template="Can you summarize the following document:\n\n{markdown_content}"
#             )
#             chain = LLMChain(llm=llm, prompt=prompt)
#             summary = chain.run(content=markdown_content)
#             logger.info(f"Generated summary for {file.filename}.")
            
#             results.append({
#                 "filename": file.filename,
#                 "summary": summary
#             })
#         except Exception as e:
#             logger.error(f"Error processing file {file.filename}: {str(e)}")
#             results.append({
#                 "filename": file.filename,
#                 "error": str(e)
#             })
#         finally:
#             if os.path.exists(temp_file_path):
#                 os.remove(temp_file_path)
#                 logger.info(f"Deleted temporary file: {temp_file_path}")
    
#     logger.info("File upload request processing complete.")
#     return JSONResponse(content={"results": results})
