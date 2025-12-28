from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uuid
import time
from queue import Queue
from threading import Lock
import threading
import subprocess
import os
import requests

from api.db import (
    init_db,
    insert_request,
    update_request,
    fetch_request,
    fetch_all_requests,
    fetch_logs
)

# =========================
# App
# =========================

app = FastAPI(
    title="FirmAE API Service",
    description="API wrapper for FirmAE firmware emulation",
    version="0.1"
)

# =========================
# Queue system (NO PARALLEL)
# =========================

JOB_QUEUE = Queue()
WORKER_LOCK = Lock()
JOB_TIMEOUT = 300  # seconds

FIRMWARE_DIR = "/tmp/firmae_firmware"
os.makedirs(FIRMWARE_DIR, exist_ok=True)

# =========================
# Worker
# =========================

def job_worker():
    while True:
        request_id = JOB_QUEUE.get()
        if request_id is None:
            break

        with WORKER_LOCK:
            update_request(request_id, status="running")
            add_log(request_id, "Job started")

            start_time = time.time()

            try:
                add_log(request_id, "Preparing FirmAE execution")

                row = fetch_request(request_id)
                if not row:
                    raise RuntimeError("Request not found in DB")

                firmware_path = row[6]  # firmware column

                if not firmware_path or not os.path.exists(firmware_path):
                    raise RuntimeError("Firmware file not found")

                cmd = [
                    "sudo",
                    "./run.sh",
                    "-a",
                    "auto",
                    firmware_path
                ]

                add_log(request_id, f"Executing FirmAE: {' '.join(cmd)}")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                try:
                    stdout, stderr = process.communicate(timeout=JOB_TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()
                    raise TimeoutError("FirmAE execution timed out")

                if process.returncode != 0:
                    raise RuntimeError(stderr.strip())

                update_request(
                    request_id,
                    status="completed",
                    result="FirmAE analysis completed"
                )

                add_log(request_id, "FirmAE execution completed successfully")

            except Exception as e:
                update_request(
                    request_id,
                    status="failed",
                    error=str(e)
                )
                add_log(request_id, f"Error: {str(e)}")

            JOB_QUEUE.task_done()


def start_worker():
    worker = threading.Thread(target=job_worker, daemon=True)
    worker.start()

# =========================
# Startup
# =========================

@app.on_event("startup")
def startup_event():
    init_db()
    start_worker()

# =========================
# APIs
# =========================

@app.get("/health")
def health_check():
    return {"status": "ok"}

# -------------------------
# Start analysis
# -------------------------

@app.post("/analyze")
def analyze_firmware(
    firmware_url: str = Form(None),
    file: UploadFile = File(None)
):
    if not firmware_url and not file:
        raise HTTPException(
            status_code=400,
            detail="Either firmware file or firmware_url must be provided"
        )

    if firmware_url and file:
        raise HTTPException(
            status_code=400,
            detail="Provide only one: firmware file OR firmware_url"
        )

    request_id = str(uuid.uuid4())
    firmware_path = f"{FIRMWARE_DIR}/{request_id}.bin"

    if file:
        with open(firmware_path, "wb") as f:
            f.write(file.file.read())

    if firmware_url:
        try:
            r = requests.get(firmware_url, timeout=30)
            r.raise_for_status()
            with open(firmware_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download firmware: {str(e)}"
            )

    insert_request(request_id, firmware_path)
    add_log(request_id, "Request received")
    JOB_QUEUE.put(request_id)

    return {
        "request_id": request_id,
        "status": "queued",
        "data": None,
        "error": None
    }

# -------------------------
# Status
# -------------------------

@app.get("/status/{request_id}")
def get_status(request_id: str):
    row = fetch_request(request_id)

    if not row:
        return {
            "request_id": request_id,
            "status": "not_found",
            "data": None,
            "error": "Request not found"
        }

    return {
        "request_id": row[0],
        "status": row[1],
        "data": {
            "created_at": row[2],
            "updated_at": row[3]
        },
        "error": row[5]
    }

# -------------------------
# List all requests
# -------------------------

@app.get("/requests")
def list_requests():
    rows = fetch_all_requests()

    return {
        "count": len(rows),
        "requests": [
            {
                "request_id": r[0],
                "status": r[1],
                "created_at": r[2],
                "updated_at": r[3]
            }
            for r in rows
        ]
    }

# -------------------------
# Logs
# -------------------------

@app.get("/logs/{request_id}")
def get_logs(request_id: str):
    logs = fetch_logs(request_id)

    if not logs:
        return {
            "request_id": request_id,
            "status": "not_found",
            "data": [],
            "error": "No logs found"
        }

    return {
        "request_id": request_id,
        "status": "ok",
        "data": [
            {"timestamp": ts, "message": msg}
            for ts, msg in logs
        ],
        "error": None
    }

# -------------------------
# Result
# -------------------------

@app.get("/result/{request_id}")
def get_result(request_id: str):
    row = fetch_request(request_id)

    if not row:
        return {
            "request_id": request_id,
            "status": "not_found",
            "data": None,
            "error": "Request not found"
        }

    return {
        "request_id": row[0],
        "status": row[1],
        "data": {
            "result": row[4]
        },
        "error": row[5]
    }
