#!/usr/bin/env python3
"""
Flask Security Scan Results Server
Provides REST API endpoints to serve dummy scan results from Sonar, Fortify, and Nexus
"""
import os
import sys
from datetime import datetime

file_root = os.path.dirname(os.path.abspath(__file__))
path_list = [
    file_root,
    os.path.dirname(file_root)
]
for path in path_list:
    if path not in sys.path:
        sys.path.append(path)

from flask import Flask, jsonify, request
from utils.scan_results import (get_fortify_scan_results_impl,
                                get_nexus_scan_results_impl,
                                get_sonar_scan_results_impl,
                                get_all_scan_results as get_all_scan_results_impl)

app = Flask(__name__)


# Flask API Routes
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Security Scan Results API",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/scans/sonar', methods=['GET'])
def get_sonar_results():
    """Get SonarQube scan results"""
    project_key = request.args.get('project_key', 'default-project')
    try:
        results = get_sonar_scan_results_impl(project_key)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scans/fortify', methods=['GET'])
def get_fortify_results():
    """Get Fortify scan results"""
    application_name = request.args.get('application_name', 'default-app')
    try:
        results = get_fortify_scan_results_impl(application_name)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scans/nexus', methods=['GET'])
def get_nexus_results():
    """Get Nexus IQ scan results"""
    repository_name = request.args.get('repository_name', 'default-repo')
    try:
        results = get_nexus_scan_results_impl(repository_name)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scans/all', methods=['GET'])
def get_all_results():
    """Get consolidated scan results from all tools"""
    project_identifier = request.args.get('project_identifier', 'default-project')

    try:
        return jsonify(get_all_scan_results_impl(project_identifier=project_identifier))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Starting Security Scan Results Flask Server...")
    print("Available endpoints:")
    print("  GET /api/scans/sonar?project_key=<key>")
    print("  GET /api/scans/fortify?application_name=<name>")
    print("  GET /api/scans/nexus?repository_name=<name>")
    print("  GET /api/scans/all?project_identifier=<identifier>")
    app.run(debug=True, host='0.0.0.0', port=5001)
