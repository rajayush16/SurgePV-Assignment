from app.crud.users import create_user


def test_reports_endpoints(client, db_session):
    user_one = create_user(db_session, "Dev A", "dev.a@example.com")
    user_two = create_user(db_session, "Dev B", "dev.b@example.com")
    db_session.commit()

    issue_one = client.post("/issues", json={"title": "A1", "assignee_id": user_one.id}).json()
    issue_two = client.post("/issues", json={"title": "A2", "assignee_id": user_one.id}).json()
    issue_three = client.post("/issues", json={"title": "B1", "assignee_id": user_two.id}).json()

    client.patch(
        f"/issues/{issue_one['id']}",
        json={"status": "RESOLVED", "version": issue_one["version"]},
    )

    top = client.get("/reports/top-assignees").json()
    assert len(top["items"]) >= 2
    assert top["items"][0]["assignee_id"] == user_one.id

    latency = client.get("/reports/latency").json()
    assert latency["resolved_count"] >= 1
