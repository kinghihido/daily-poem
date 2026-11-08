# -*- coding: utf-8 -*-
"""当 github.com:443 不可达时的推送兜底：把本地 HEAD 通过 GitHub REST API 写成一次提交。"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

REPO = "kinghihido/daily-poem"
BRANCH = "main"


def token():
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def api(method, path, payload=None, tok=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path,
        method=method,
        data=data,
        headers={
            "Authorization": "Bearer " + tok,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "daily-poem-automation",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def main():
    tok = token()
    # 父提交取远端当前 head：网络不通时本地无法 fetch，本地 history 可能与远端不一致
    base = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}", tok=tok)["object"]["sha"]
    msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()
    files = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], text=True
    ).split()

    base_tree = api("GET", f"/repos/{REPO}/git/commits/{base}", tok=tok)["tree"]["sha"]

    entries = []
    for f in files:
        if os.path.exists(f):
            content = base64.b64encode(open(f, "rb").read()).decode("ascii")
            blob = api(
                "POST",
                f"/repos/{REPO}/git/blobs",
                {"content": content, "encoding": "base64"},
                tok=tok,
            )["sha"]
            entries.append({"path": f, "mode": "100644", "type": "blob", "sha": blob})
        else:
            entries.append({"path": f, "mode": "100644", "type": "blob", "sha": None})

    tree = api(
        "POST",
        f"/repos/{REPO}/git/trees",
        {"base_tree": base_tree, "tree": entries},
        tok=tok,
    )["sha"]

    commit = api(
        "POST",
        f"/repos/{REPO}/git/commits",
        {"message": msg, "tree": tree, "parents": [base]},
        tok=tok,
    )["sha"]

    api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit, "force": False}, tok=tok)

    head = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}", tok=tok)["object"]["sha"]
    print("pushed via api:", commit)
    print("remote head now:", head)
    if head != commit:
        sys.exit("MISMATCH: remote head differs from new commit")


if __name__ == "__main__":
    main()
