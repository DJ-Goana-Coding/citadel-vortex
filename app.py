from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get('/')
def health():
    return {'status': 'SUCCESS', 'message': 'TIA Node Active'}

if __name__ == '__main__':
    # PORT 7860 is the Hard-Iron requirement for Hugging Face
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))
