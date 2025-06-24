#!/usr/bin/env python3
"""
Flask Security Scan Results Server
Provides REST API endpoints to serve dummy scan results from Sonar, Fortify, and Nexus
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import concurrent.futures

from flask import Flask, jsonify, request

app = Flask(__name__)


def generate_random_severity():
    """Generate random severity level"""
    return random.choice(["Critical", "High", "Medium", "Low", "Info"])


def generate_random_status():
    """Generate random scan status"""
    return random.choice(["Completed", "In Progress", "Failed", "Queued"])


def generate_random_date(days_back=30):
    """Generate random date within last N days"""
    base_date = datetime.now()
    random_days = random.randint(0, days_back)
    return (base_date - timedelta(days=random_days)).isoformat()


def _get_sonar_scan_results_impl(project_key: str = "default-project") -> Dict[str, Any]:
    """
    Internal implementation for SonarQube scan results.
    """
    # Generate random metrics
    lines_of_code = random.randint(1000, 100000)
    coverage = round(random.uniform(40, 95), 1)

    # Generate random issues
    issues = []
    issue_types = [
        "Code Smell", "Bug", "Vulnerability", "Security Hotspot",
        "Maintainability Issue", "Reliability Issue"
    ]

    for _ in range(random.randint(5, 25)):
        issues.append({
            "key": f"sonar-{uuid.uuid4().hex[:8]}",
            "type": random.choice(issue_types),
            "severity": generate_random_severity(),
            "component": f"src/main/java/com/example/{random.choice(['Controller', 'Service', 'Repository', 'Model'])}.java",
            "line": random.randint(1, 500),
            "message": random.choice([
                "Potential SQL injection vulnerability",
                "Unused import should be removed",
                "Method complexity is too high",
                "Hardcoded credentials detected",
                "Potential XSS vulnerability",
                "Memory leak possible",
                "Dead code should be removed"
            ]),
            "effort": f"{random.randint(5, 120)}min",
            "debt": f"{random.randint(1, 8)}h",
            "created_date": generate_random_date(7)
        })

    # Generate quality gates
    quality_gate = {
        "status": random.choice(["PASSED", "FAILED", "WARNING"]),
        "conditions": [
            {
                "metric": "coverage",
                "operator": "LT",
                "threshold": "80.0",
                "actual_value": str(coverage),
                "status": "PASSED" if coverage >= 80 else "FAILED"
            },
            {
                "metric": "new_vulnerabilities",
                "operator": "GT",
                "threshold": "0",
                "actual_value": str(len([i for i in issues if i["type"] == "Vulnerability"])),
                "status": random.choice(["PASSED", "FAILED"])
            }
        ]
    }

    return {
        "scan_id": f"sonar-{uuid.uuid4().hex}",
        "project_key": project_key,
        "project_name": f"Project {project_key.title()}",
        "scan_date": generate_random_date(1),
        "status": generate_random_status(),
        "metrics": {
            "lines_of_code": lines_of_code,
            "coverage": coverage,
            "duplicated_lines_density": round(random.uniform(0, 15), 1),
            "maintainability_rating": random.choice(["A", "B", "C", "D", "E"]),
            "reliability_rating": random.choice(["A", "B", "C", "D", "E"]),
            "security_rating": random.choice(["A", "B", "C", "D", "E"]),
            "technical_debt": f"{random.randint(1, 50)}h"
        },
        "issues": issues,
        "issue_counts": {
            "total": len(issues),
            "critical": len([i for i in issues if i["severity"] == "Critical"]),
            "high": len([i for i in issues if i["severity"] == "High"]),
            "medium": len([i for i in issues if i["severity"] == "Medium"]),
            "low": len([i for i in issues if i["severity"] == "Low"]),
            "info": len([i for i in issues if i["severity"] == "Info"])
        },
        "quality_gate": quality_gate,
        "dashboard_url": f"https://sonarqube.company.com/dashboard?id={project_key}"
    }


def _get_fortify_scan_results_impl(application_name: str = "default-app") -> Dict[str, Any]:
    """
    Internal implementation for Fortify scan results.
    """
    # Generate random vulnerabilities
    vulnerabilities = []
    vulnerability_categories = [
        "Cross-Site Scripting", "SQL Injection", "Path Manipulation",
        "Command Injection", "LDAP Injection", "XML Injection",
        "Buffer Overflow", "Resource Injection", "Privacy Violation",
        "Weak Cryptographic Hash", "Insecure Randomness", "Trust Boundary Violation"
    ]

    for _ in range(random.randint(3, 20)):
        vulnerabilities.append({
            "instance_id": f"fortify-{uuid.uuid4().hex[:8]}",
            "category": random.choice(vulnerability_categories),
            "severity": generate_random_severity(),
            "confidence": random.choice(["High", "Medium", "Low"]),
            "impact": round(random.uniform(1, 5), 1),
            "likelihood": round(random.uniform(1, 5), 1),
            "file_path": f"src/main/java/com/example/{random.choice(['web', 'service', 'dao', 'util'])}/{random.choice(['UserController', 'AuthService', 'DatabaseDAO', 'ValidationUtil'])}.java",
            "line_number": random.randint(1, 500),
            "function_name": random.choice(
                ["authenticate", "processInput", "executeQuery", "validateUser", "encryptData"]),
            "description": random.choice([
                "User input is not properly validated before being used in SQL query",
                "Data from user input is not encoded before output to web page",
                "File path constructed from user input without proper validation",
                "Cryptographic hash function is weak and vulnerable to attacks",
                "Random number generator is not cryptographically secure"
            ]),
            "recommendation": "Implement proper input validation and output encoding",
            "cwe_id": random.choice([79, 89, 22, 78, 90, 91, 120, 134, 311, 330]),
            "owasp_category": random.choice(["A03:2021", "A02:2021", "A01:2021", "A04:2021", "A06:2021"]),
            "first_detected": generate_random_date(30),
            "last_seen": generate_random_date(3)
        })

    # Generate scan statistics
    total_files_scanned = random.randint(100, 1000)
    scan_duration = random.randint(300, 3600)  # seconds

    return {
        "scan_id": f"fortify-{uuid.uuid4().hex}",
        "application_name": application_name,
        "version": f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
        "scan_date": generate_random_date(1),
        "status": generate_random_status(),
        "scan_statistics": {
            "total_files_scanned": total_files_scanned,
            "lines_of_code": random.randint(50000, 500000),
            "scan_duration_seconds": scan_duration,
            "scan_duration_formatted": f"{scan_duration // 60}m {scan_duration % 60}s",
            "fortify_version": f"22.{random.randint(1, 2)}.{random.randint(0, 3)}"
        },
        "vulnerabilities": vulnerabilities,
        "vulnerability_counts": {
            "total": len(vulnerabilities),
            "critical": len([v for v in vulnerabilities if v["severity"] == "Critical"]),
            "high": len([v for v in vulnerabilities if v["severity"] == "High"]),
            "medium": len([v for v in vulnerabilities if v["severity"] == "Medium"]),
            "low": len([v for v in vulnerabilities if v["severity"] == "Low"]),
            "info": len([v for v in vulnerabilities if v["severity"] == "Info"])
        },
        "category_breakdown": {
            category: len([v for v in vulnerabilities if v["category"] == category])
            for category in set(v["category"] for v in vulnerabilities)
        },
        "risk_metrics": {
            "fortify_priority_order": round(random.uniform(1, 5), 2),
            "business_criticality": random.choice(["High", "Medium", "Low"]),
            "overall_risk_score": round(random.uniform(1, 10), 1)
        },
        "dashboard_url": f"https://fortify.company.com/ssc/html/ssc/index.jsp#!/version/{random.randint(1000, 9999)}/fix"
    }


def _get_nexus_scan_results_impl(repository_name: str = "default-repo") -> Dict[str, Any]:
    """
    Internal implementation for Nexus IQ scan results.
    """
    # Generate random components with vulnerabilities
    components = []
    component_types = ["maven", "npm", "pypi", "nuget", "docker"]

    for _ in range(random.randint(5, 30)):
        component_type = random.choice(component_types)
        if component_type == "maven":
            component_name = f"org.apache.{random.choice(['commons', 'http', 'logging'])}"
            package_name = f"{component_name}:{random.choice(['commons-lang3', 'httpclient', 'log4j-core'])}"
        elif component_type == "npm":
            package_name = random.choice(['lodash', 'express', 'react', 'axios', 'moment'])
        elif component_type == "pypi":
            package_name = random.choice(['requests', 'django', 'flask', 'numpy', 'pandas'])
        elif component_type == "nuget":
            package_name = random.choice(['Newtonsoft.Json', 'Microsoft.AspNetCore', 'Serilog'])
        else:  # docker
            package_name = random.choice(['alpine', 'ubuntu', 'nginx', 'node', 'python'])

        version = f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 10)}"

        # Generate vulnerabilities for this component
        vulnerabilities = []
        for _ in range(random.randint(0, 5)):
            vulnerabilities.append({
                "cve_id": f"CVE-{random.randint(2020, 2024)}-{random.randint(1000, 9999)}",
                "cvss_score": round(random.uniform(1, 10), 1),
                "severity": generate_random_severity(),
                "summary": random.choice([
                    "Remote code execution vulnerability",
                    "Cross-site scripting vulnerability",
                    "Denial of service vulnerability",
                    "Information disclosure vulnerability",
                    "Authentication bypass"
                ]),
                "published_date": generate_random_date(365),
                "modified_date": generate_random_date(30)
            })

        components.append({
            "component_id": f"{component_type}-{uuid.uuid4().hex[:8]}",
            "package_name": package_name,
            "version": version,
            "type": component_type,
            "license": random.choice([
                "Apache-2.0", "MIT", "GPL-3.0", "BSD-3-Clause",
                "ISC", "LGPL-2.1", "MPL-2.0", "Unlicense", "EPL-1.0"
            ]),
            "direct_dependency": random.choice([True, False]),
            "vulnerabilities": vulnerabilities,
            "vulnerability_count": len(vulnerabilities),
            "highest_cvss": max([v["cvss_score"] for v in vulnerabilities]) if vulnerabilities else 0,
            "policy_violations": random.randint(0, 3),
            "license_threat_level": random.choice(["None", "Low", "Medium", "High"]),
            "age_months": random.randint(1, 60)
        })

    # Generate policy violations
    policy_violations = []
    violation_types = ["Security", "License", "Architecture", "Quality"]

    for _ in range(random.randint(0, 10)):
        policy_violations.append({
            "violation_id": f"policy-{uuid.uuid4().hex[:8]}",
            "type": random.choice(violation_types),
            "severity": generate_random_severity(),
            "policy_name": random.choice([
                "Critical Security Policy", "License Compliance Policy",
                "Architecture Standards", "Component Quality Policy"
            ]),
            "component": random.choice(components)["package_name"] if components else "unknown",
            "description": random.choice([
                "Component has critical security vulnerabilities",
                "License is not approved for commercial use",
                "Component violates architecture standards",
                "Component quality metrics below threshold"
            ]),
            "detected_date": generate_random_date(14)
        })

    return {
        "scan_id": f"nexus-{uuid.uuid4().hex}",
        "repository_name": repository_name,
        "application_name": f"App-{repository_name}",
        "scan_date": generate_random_date(1),
        "status": generate_random_status(),
        "stage": random.choice(["develop", "build", "stage-release", "release", "operate"]),
        "summary": {
            "total_components": len(components),
            "components_with_vulnerabilities": len([c for c in components if c["vulnerability_count"] > 0]),
            "total_vulnerabilities": sum(c["vulnerability_count"] for c in components),
            "critical_vulnerabilities": len(
                [c for comp in components for c in comp["vulnerabilities"] if c["severity"] == "Critical"]),
            "high_vulnerabilities": len(
                [c for comp in components for c in comp["vulnerabilities"] if c["severity"] == "High"]),
            "policy_violations": len(policy_violations),
            "license_issues": len([c for c in components if c["license_threat_level"] in ["Medium", "High"]])
        },
        "components": components,
        "policy_violations": policy_violations,
        "risk_metrics": {
            "application_risk_score": round(random.uniform(1, 100), 1),
            "policy_evaluation": random.choice(["Pass", "Warn", "Fail"]),
            "open_policy_violations": len([p for p in policy_violations if p["severity"] in ["Critical", "High"]]),
            "legacy_components": len([c for c in components if c["age_months"] > 24])
        },
        "license_summary": {
            license: len([c for c in components if c["license"] == license])
            for license in set(c["license"] for c in components)
        },
        "dashboard_url": f"https://nexus-iq.company.com/ui/links/application/{repository_name}/report/{uuid.uuid4().hex[:8]}"
    }


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
        results = _get_sonar_scan_results_impl(project_key)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scans/fortify', methods=['GET'])
def get_fortify_results():
    """Get Fortify scan results"""
    application_name = request.args.get('application_name', 'default-app')
    try:
        results = _get_fortify_scan_results_impl(application_name)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scans/nexus', methods=['GET'])
def get_nexus_results():
    """Get Nexus IQ scan results"""
    repository_name = request.args.get('repository_name', 'default-repo')
    try:
        results = _get_nexus_scan_results_impl(repository_name)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scans/all', methods=['GET'])
def get_all_results():
    """Get consolidated scan results from all tools"""
    project_identifier = request.args.get('project_identifier', 'default-project')
    
    try:
        # Call the internal implementation functions in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all three scan functions to run in parallel
            sonar_future = executor.submit(_get_sonar_scan_results_impl, project_identifier)
            fortify_future = executor.submit(_get_fortify_scan_results_impl, project_identifier)
            nexus_future = executor.submit(_get_nexus_scan_results_impl, project_identifier)

            # Wait for all results to complete
            sonar_results = sonar_future.result()
            fortify_results = fortify_future.result()
            nexus_results = nexus_future.result()

        # Calculate consolidated metrics
        total_issues = (
                sonar_results["issue_counts"]["total"] +
                fortify_results["vulnerability_counts"]["total"] +
                nexus_results["summary"]["total_vulnerabilities"]
        )

        critical_issues = (
                sonar_results["issue_counts"]["critical"] +
                fortify_results["vulnerability_counts"]["critical"] +
                nexus_results["summary"]["critical_vulnerabilities"]
        )

        consolidated_results = {
            "project_identifier": project_identifier,
            "consolidated_scan_date": datetime.now().isoformat(),
            "summary": {
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "tools_scanned": 3,
                "overall_risk_level": "Critical" if critical_issues > 5 else "High" if critical_issues > 0 else "Medium"
            },
            "sonar_results": sonar_results,
            "fortify_results": fortify_results,
            "nexus_results": nexus_results,
            "recommendations": [
                "Address critical security vulnerabilities identified by Fortify",
                "Improve code coverage to meet quality gate requirements",
                "Update components with known vulnerabilities in Nexus IQ",
                "Review and remediate policy violations",
                "Implement secure coding practices to prevent future issues"
            ]
        }
        
        return jsonify(consolidated_results)
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
