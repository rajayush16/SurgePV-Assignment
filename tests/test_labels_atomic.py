def test_labels_replace_atomic(client):
    issue = client.post("/issues", json={"title": "Label update"}).json()

    response = client.put(f"/issues/{issue['id']}/labels", json={"labels": ["bug", "urgent"]})
    assert response.status_code == 200
    assert sorted([label["name"] for label in response.json()["labels"]]) == ["bug", "urgent"]

    replace = client.put(f"/issues/{issue['id']}/labels", json={"labels": ["enhancement"]})
    assert replace.status_code == 200
    final_labels = [label["name"] for label in replace.json()["labels"]]
    assert final_labels == ["enhancement"]
