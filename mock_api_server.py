"""
Mock MiroFish API Server for Testing
Simulates MiroFish API responses without requiring camel-oasis
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Mock data storage
simulations = {}
agents = {}
debates = {}
predictions = {}


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "mirofish-mock-api",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            }
        ),
        200,
    )


@app.route("/api/simulations", methods=["GET"])
def list_simulations():
    """List all simulations"""
    return (
        jsonify({"simulations": list(simulations.values()), "total": len(simulations)}),
        200,
    )


@app.route("/api/simulations", methods=["POST"])
def create_simulation():
    """Create a new simulation"""
    data = request.json
    sim_id = str(uuid.uuid4())

    simulation = {
        "id": sim_id,
        "name": data.get("name", "Untitled Simulation"),
        "description": data.get("description", ""),
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "agents": [],
        "debates": [],
        "predictions": [],
    }

    simulations[sim_id] = simulation
    return jsonify(simulation), 201


@app.route("/api/simulations/<sim_id>", methods=["GET"])
def get_simulation(sim_id):
    """Get simulation details"""
    if sim_id not in simulations:
        return jsonify({"error": "Simulation not found"}), 404
    return jsonify(simulations[sim_id]), 200


@app.route("/api/simulations/<sim_id>/agents", methods=["POST"])
def create_agent(sim_id):
    """Create an agent in a simulation"""
    if sim_id not in simulations:
        return jsonify({"error": "Simulation not found"}), 404

    data = request.json
    agent_id = str(uuid.uuid4())

    agent = {
        "id": agent_id,
        "simulation_id": sim_id,
        "name": data.get("name", "Agent"),
        "role": data.get("role", "analyst"),
        "personality": data.get("personality", ""),
        "created_at": datetime.now().isoformat(),
    }

    agents[agent_id] = agent
    simulations[sim_id]["agents"].append(agent_id)
    return jsonify(agent), 201


@app.route("/api/simulations/<sim_id>/debates", methods=["POST"])
def create_debate(sim_id):
    """Create a debate in a simulation"""
    if sim_id not in simulations:
        return jsonify({"error": "Simulation not found"}), 404

    data = request.json
    debate_id = str(uuid.uuid4())

    debate = {
        "id": debate_id,
        "simulation_id": sim_id,
        "topic": data.get("topic", "Untitled Debate"),
        "status": "in_progress",
        "rounds": data.get("rounds", 3),
        "current_round": 1,
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    debates[debate_id] = debate
    simulations[sim_id]["debates"].append(debate_id)
    return jsonify(debate), 201


@app.route("/api/debates/<debate_id>", methods=["GET"])
def get_debate(debate_id):
    """Get debate details"""
    if debate_id not in debates:
        return jsonify({"error": "Debate not found"}), 404
    return jsonify(debates[debate_id]), 200


@app.route("/api/debates/<debate_id>/messages", methods=["POST"])
def add_debate_message(debate_id):
    """Add a message to a debate"""
    if debate_id not in debates:
        return jsonify({"error": "Debate not found"}), 404

    data = request.json
    message = {
        "id": str(uuid.uuid4()),
        "agent_id": data.get("agent_id"),
        "content": data.get("content", ""),
        "timestamp": datetime.now().isoformat(),
    }

    debates[debate_id]["messages"].append(message)
    debates[debate_id]["updated_at"] = datetime.now().isoformat()
    return jsonify(message), 201


@app.route("/api/debates/<debate_id>/conclude", methods=["POST"])
def conclude_debate(debate_id):
    """Conclude a debate and generate prediction"""
    if debate_id not in debates:
        return jsonify({"error": "Debate not found"}), 404

    debate = debates[debate_id]
    debate["status"] = "concluded"

    # Generate mock prediction
    prediction_id = str(uuid.uuid4())
    prediction = {
        "id": prediction_id,
        "debate_id": debate_id,
        "topic": debate["topic"],
        "consensus": "The debate reached consensus through multi-agent discussion",
        "confidence": 0.85,
        "key_points": [
            "Point 1 from agent discussion",
            "Point 2 from agent discussion",
            "Point 3 from agent discussion",
        ],
        "created_at": datetime.now().isoformat(),
    }

    predictions[prediction_id] = prediction
    debate["prediction_id"] = prediction_id

    return jsonify({"debate": debate, "prediction": prediction}), 200


@app.route("/api/predictions/<prediction_id>", methods=["GET"])
def get_prediction(prediction_id):
    """Get prediction details"""
    if prediction_id not in predictions:
        return jsonify({"error": "Prediction not found"}), 404
    return jsonify(predictions[prediction_id]), 200


@app.route("/api/status", methods=["GET"])
def status():
    """Get system status"""
    return (
        jsonify(
            {
                "status": "operational",
                "simulations_count": len(simulations),
                "agents_count": len(agents),
                "debates_count": len(debates),
                "predictions_count": len(predictions),
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )


@app.route("/api/simulation/history", methods=["GET"])
def simulation_history():
    """Get simulation history"""
    limit = request.args.get("limit", 20, type=int)
    history = [
        {
            "id": sim_id,
            "name": sim.get("name", "Untitled"),
            "status": sim.get("status", "completed"),
            "created_at": sim.get("created_at", datetime.now().isoformat()),
        }
        for sim_id, sim in list(simulations.items())[:limit]
    ]
    return jsonify({"history": history, "total": len(history)}), 200


@app.route("/api/simulation/list", methods=["GET"])
def simulation_list():
    """List all simulations"""
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    sim_list = list(simulations.values())[offset : offset + limit]
    return (
        jsonify(
            {
                "simulations": sim_list,
                "total": len(simulations),
                "limit": limit,
                "offset": offset,
            }
        ),
        200,
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Starting Mock MiroFish API Server on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=True)
