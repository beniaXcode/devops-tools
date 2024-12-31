# app.py
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost/dockerfile_db'
db = SQLAlchemy(app)

class DockerfileHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/api/generate', methods=['POST'])
def generate_dockerfile():
    data = request.json
    content = []
    
    if 'from' in data:
        content.append(f"FROM {data['from']}")
    
    if 'workdir' in data:
        content.append(f"WORKDIR {data['workdir']}")
    
    if 'copy' in data:
        for copy_cmd in data['copy']:
            content.append(f"COPY {copy_cmd['src']} {copy_cmd['dest']}")
    
    if 'run' in data:
        for run_cmd in data['run']:
            content.append(f"RUN {run_cmd}")
    
    if 'cmd' in data:
        for cmd in data['cmd']:
            content.append(f"CMD {cmd}")
    
    dockerfile_content = '\n'.join(content)
    
    # Save to history
    history = DockerfileHistory(content=dockerfile_content)
    db.session.add(history)
    db.session.commit()
    
    return jsonify({
        "content": dockerfile_content,
        "id": history.id
    }), 200

@app.route('/api/download/<int:id>', methods=['GET'])
def download_dockerfile(id):
    dockerfile = DockerfileHistory.query.get_or_404(id)
    buffer = io.BytesIO(dockerfile.content.encode('utf-8'))
    return send_file(
        buffer,
        mimetype='text/plain',
        as_attachment=True,
        download_name='Dockerfile'
    )

@app.route('/api/history', methods=['GET'])
def get_history():
    history = DockerfileHistory.query.order_by(DockerfileHistory.created_at.desc()).limit(10).all()
    return jsonify([{
        "id": h.id,
        "content": h.content,
        "created_at": h.created_at.isoformat()
    } for h in history])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001)