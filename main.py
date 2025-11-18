import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Survey, Response as SurveyResponse

app = FastAPI(title="LuxSurvey API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IdResponse(BaseModel):
    id: str


def to_dict(doc):
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


@app.get("/")
def read_root():
    return {"message": "LuxSurvey Backend Running"}


@app.get("/test")
def test_database():
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            resp["database"] = "✅ Available"
            resp["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            resp["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                resp["collections"] = db.list_collection_names()
                resp["connection_status"] = "Connected"
                resp["database"] = "✅ Connected & Working"
            except Exception as e:
                resp["database"] = f"⚠️ Connected but Error: {str(e)[:60]}"
        else:
            resp["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        resp["database"] = f"❌ Error: {str(e)[:60]}"
    return resp


# Survey CRUD
@app.post("/api/surveys", response_model=IdResponse)
async def create_survey(survey: Survey):
    try:
        new_id = create_document("survey", survey)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/surveys", response_model=List[dict])
async def list_surveys(status: Optional[str] = None, owner_id: Optional[str] = None):
    filter_q = {}
    if status:
        filter_q["status"] = status
    if owner_id:
        filter_q["owner_id"] = owner_id
    try:
        docs = get_documents("survey", filter_q)
        return [to_dict(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/surveys/{survey_id}")
async def get_survey(survey_id: str):
    try:
        doc = db["survey"].find_one({"_id": ObjectId(survey_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Survey not found")
        return to_dict(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    theme: Optional[dict] = None
    questions: Optional[list] = None


@app.patch("/api/surveys/{survey_id}")
async def update_survey(survey_id: str, payload: SurveyUpdate):
    try:
        update = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        if not update:
            return {"updated": False}
        db["survey"].update_one({"_id": ObjectId(survey_id)}, {"$set": update})
        doc = db["survey"].find_one({"_id": ObjectId(survey_id)})
        return to_dict(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/surveys/{survey_id}")
async def delete_survey(survey_id: str):
    try:
        res = db["survey"].delete_one({"_id": ObjectId(survey_id)})
        return {"deleted": res.deleted_count == 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Responses
@app.post("/api/surveys/{survey_id}/responses", response_model=IdResponse)
async def submit_response(survey_id: str, data: SurveyResponse):
    try:
        if survey_id != data.survey_id:
            raise HTTPException(status_code=400, detail="survey_id mismatch")
        new_id = create_document("response", data)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/surveys/{survey_id}/responses")
async def list_responses(survey_id: str):
    try:
        docs = get_documents("response", {"survey_id": survey_id})
        return [to_dict(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Schema exposure for admin viewers
@app.get("/schema")
async def schema_info():
    return {
        "collections": [
            {"name": "survey"},
            {"name": "response"},
            {"name": "user"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
