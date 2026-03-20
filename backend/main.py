from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from agent import run_agent

app = FastAPI(title="ShadowTrace API", version="1.0")

# CORS fix — allows React frontend to talk to FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hard limit for demo defense: 20MB max upload, but we only process a 3MB sample
MAX_FILE_SIZE = 20 * 1024 * 1024  
MAX_PROCESS_SIZE = 3 * 1024 * 1024  

def safe_read_and_decode(file: UploadFile) -> str:
    """Safely reads file with size limits and controlled sampling."""
    if not file:
        return "{}"
    
    # Check full file size without loading everything into memory
    file.file.seek(0, 2)  # jump to end of file
    size = file.file.tell() # get the byte position (size)
    file.file.seek(0)     # reset pointer back to beginning
    
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File {file.filename} exceeds the 20MB demo limit.")

    # Read only a safe, representative chunk for processing
    content = file.file.read(MAX_PROCESS_SIZE)
    
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        # Fallback for weird Windows encodings or binary files
        return content.decode('latin-1', errors='ignore')

# Health check route — confirms server is running
@app.get("/")
def root():
    return {"status": "ShadowTrace backend is running"}

# Main scan route — receives all user input and runs full agent pipeline
@app.post("/scan")
async def scan(
    email: str = Form(...),
    sms_headers: str = Form(...),
    myactivity_file: UploadFile = File(None),
    location_file: UploadFile = File(None)
):
    try:
        # Safe read, size check, and decode (with 3MB representative sampling)
        myactivity_content = safe_read_and_decode(myactivity_file)
        location_content = safe_read_and_decode(location_file)

        # Run full agent pipeline
        result = run_agent(
            email=email,
            myactivity_content=myactivity_content,
            location_content=location_content,
            sms_headers=sms_headers
        )

        return JSONResponse(content=result)

    except ValueError as ve:
        # Caught a file size violation (returns clean 400-level logic)
        return JSONResponse(
            status_code=400,
            content={"error": str(ve), "status": "failed"}
        )
    except Exception as e:
        # Ultimate fallback for unknown server errors
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )

# Sample data route — loads pre-built demo data
@app.get("/sample")
def get_sample_data():
    return {
        "email": "rahul.sharma@gmail.com",
        "sms_headers": "AD-HDFCBK\nJM-ZOMATO\nCP-PAYTM\nAD-AIRTEL\nBZ-BYJUS\nAD-JIORMS\nCP-PHONPE\nJM-SWIGGY\nVM-IRCTC\nAD-PRACTO\nAD-ICICIB\nCP-GROWW\nJM-BIGBSK\nAD-UIADAS\nAD-TRULCR\nBZ-UNACAD\nAD-LICIND\nVM-OLACAB\nAD-UBERIN\nJM-MYNTRA",
        "message": "Load this sample data to run the demo"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)