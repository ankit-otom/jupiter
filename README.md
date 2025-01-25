# jupiter

Python service  


## Setup
1. Initialize a Virtual Environment
python3 -m venv env
source env/bin/activate

1. Install Required Libraries
pip install fastapi uvicorn docling langchain openai python-multipart

1. Install Libraries Using requirements.txt
pip install -r requirements.txt

1. Verify Installation
python -m uvicorn app:app --reload 

## FAQ
1. If you see any error related to SSL Ceritificate while running any enpoint related to Docling then run the following command:
cd /Applications/Python\ 3.10/
./Install\ Certificates.command
