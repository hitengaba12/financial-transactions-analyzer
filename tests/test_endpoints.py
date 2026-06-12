import io

from fastapi import status


def test_upload_endpoint(client):
    csv_data = (
        "account_id,date,merchant,amount,currency,category,status\n"
        "acct-1,2026-05-01,Starbucks,$5.25,USD,Food,posted\n"
        "acct-2,2026-05-02,Amazon,$125.00,USD,Shopping,posted\n"
    )
    response = client.post(
        "/jobs/upload",
        files={"file": ("transactions.csv", csv_data, "text/csv")},
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["status"] == "queued"
    assert "job_id" in body


def test_status_endpoint_returns_job_status(client):
    csv_data = (
        "account_id,date,merchant,amount,currency,category,status\n"
        "acct-3,2026-05-03,Shell,$35.10,USD,Transport,posted\n"
    )
    upload_response = client.post(
        "/jobs/upload",
        files={"file": ("transactions.csv", csv_data, "text/csv")},
    )
    assert upload_response.status_code == status.HTTP_201_CREATED
    job_id = upload_response.json()["job_id"]

    status_response = client.get(f"/jobs/{job_id}/status")
    assert status_response.status_code == status.HTTP_200_OK
    status_body = status_response.json()
    assert status_body["job_id"] == job_id
    assert status_body["status"] in {"queued", "processing", "completed", "failed"}


def test_results_endpoint_returns_job_results(client):
    csv_data = (
        "account_id,date,merchant,amount,currency,category,status\n"
        "acct-4,2026-05-04,Netflix,$12.99,USD,Entertainment,posted\n"
    )
    upload_response = client.post(
        "/jobs/upload",
        files={"file": ("transactions.csv", csv_data, "text/csv")},
    )
    assert upload_response.status_code == status.HTTP_201_CREATED
    job_id = upload_response.json()["job_id"]

    status_response = client.get(f"/jobs/{job_id}/status")
    assert status_response.status_code == status.HTTP_200_OK

    results_response = client.get(f"/jobs/{job_id}/results")
    assert results_response.status_code == status.HTTP_200_OK
    results_body = results_response.json()
    assert "transactions" in results_body
    assert "anomalies" in results_body
    assert "category_breakdown" in results_body
    assert "summary" in results_body


def test_list_jobs_endpoint_returns_jobs(client):
    response = client.get("/jobs")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "jobs" in body
    assert isinstance(body["jobs"], list)


def test_sample_csv_contains_twenty_transactions():
    with open("sample.csv", "r", encoding="utf-8") as csv_file:
        lines = csv_file.readlines()
    assert len(lines) == 21
    assert lines[0].strip() == "account_id,date,merchant,amount,currency,category,status"
    assert "acct-020" in lines[-1]
