import os
from fastapi import FastAPI
import uvicorn


PORT = int(os.getenv("PORT", 8000))

app=FastAPI()




@app.get("/", tags=["Health Check"])
async def root():
    return {"message":"Server is running 🚀"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)








