from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

# Project Genesis Base Node


@app.get('/')
def health_check():
    return {'status': 'SUCCESS', 'message': 'TIA Node: Citadel Vortex Active'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    uvicorn.run(app, host='0.0.0.0', port=port)
