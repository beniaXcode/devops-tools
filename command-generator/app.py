# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost/commands_db'
db = SQLAlchemy(app)

class CommandTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template = db.Column(db.String(500), nullable=False)
    variables = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CommandHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/api/template', methods=['POST'])
def create_template():
    data = request.json
    template = CommandTemplate(
        template=data['template'],
        variables=data['variables']
    )
    db.session.add(template)
    db.session.commit()
    return jsonify({"id": template.id}), 201

@app.route('/api/generate', methods=['POST'])
def generate_command():
    data = request.json
    template = CommandTemplate.query.get(data['template_id'])
    if not template:
        return jsonify({"error": "Template not found"}), 404
    
    # Replace variables in template
    command = template.template
    for key, value in data['variables'].items():
        command = command.replace(f"{{{key}}}", value)
    
    # Save to history
    history = CommandHistory(command=command)
    db.session.add(history)
    db.session.commit()
    
    return jsonify({"command": command}), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    history = CommandHistory.query.order_by(CommandHistory.created_at.desc()).limit(10).all()
    return jsonify([{
        "id": h.id,
        "command": h.command,
        "created_at": h.created_at.isoformat()
    } for h in history])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000)