from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get('/')
def health():
    return {'status': 'SUCCESS', 'message': 'TIA Node Active'}

if __name__ == '__main__':
    # Force-bind to port 7860
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))
