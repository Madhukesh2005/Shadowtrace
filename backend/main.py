from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn
from agent import run_agent
from monitor import start_monitor, get_notifications, clear_notifications
from pdf_generator import generate_evidence_pdf

app = FastAPI(title="ShadowTrace API", version="1.0")

# Allow the React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_PROCESS_SIZE = 3 * 1024 * 1024

def safe_read_and_decode(file: UploadFile) -> str:
    if not file:
        return "{}"
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File {file.filename} exceeds the 20MB demo limit.")
    content = file.file.read(MAX_PROCESS_SIZE)
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        return content.decode('latin-1', errors='ignore')

@app.on_event("startup")
async def startup_event():
    start_monitor()

@app.get("/")
def root():
    return {"status": "ShadowTrace backend is running"}

@app.post("/scan")
async def scan(
    email: str = Form(...),
    sms_headers: str = Form(...),
    myactivity_file: UploadFile = File(None),
    location_file: UploadFile = File(None)
):
    try:
        myactivity_content = safe_read_and_decode(myactivity_file)
        location_content = safe_read_and_decode(location_file)
        
        result = run_agent(
            email=email,
            myactivity_content=myactivity_content,
            location_content=location_content,
            sms_headers=sms_headers
        )
        return JSONResponse(content=result)
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve), "status": "failed"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "status": "failed"})

@app.get("/sample")
def get_sample_data():
    return {
        "email": "rahul.sharma@gmail.com",
        "sms_headers": "AD-HDFCBK\nJM-ZOMATO\nCP-PAYTM\nAD-AIRTEL\nBZ-BYJUS\nAD-JIORMS\nCP-PHONPE\nJM-SWIGGY\nVM-IRCTC\nAD-PRACTO",
        "message": "Load this sample data to run the demo"
    }

@app.get("/notifications")
def get_breach_notifications():
    notifications = get_notifications()
    return {"notifications": notifications, "count": len(notifications)}

@app.delete("/notifications")
def clear_breach_notifications():
    clear_notifications()
    return {"status": "cleared"}

@app.post("/download-pdf")
async def download_pdf(request: Request):
    try:
        # Stateless design: React sends the scan data, we generate the PDF instantly
        body = await request.json()
        pdf_bytes = generate_evidence_pdf(body)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ShadowTrace_Evidence.pdf"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)