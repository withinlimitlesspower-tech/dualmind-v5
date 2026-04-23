from github import Github
from github import GithubException

def push_to_github(files: dict, repo_name: str, token: str) -> str:
    """Push files to a new GitHub repository. Returns the repo URL."""
    g = Github(token)
    user = g.get_user()
    
    # Check if repo already exists
    try:
        repo = user.get_repo(repo_name)
        # If exists, we need to update files
    except GithubException:
        # Create new repo
        repo = user.create_repo(repo_name, private=False)
    
    # Get default branch
    try:
        branch = repo.get_branch(repo.default_branch)
    except GithubException:
        # Create initial commit
        repo.create_file("README.md", "initial commit", "# AI Code Manager Generated Project")
        branch = repo.get_branch(repo.default_branch)
    
    for filepath, content in files.items():
        try:
            # Check if file exists
            contents = repo.get_contents(filepath, ref=branch.commit.sha)
            # Update file
            repo.update_file(filepath, f"Update {filepath}", content, contents.sha, branch=branch.name)
        except GithubException:
            # Create new file
            repo.create_file(filepath, f"Add {filepath}", content, branch=branch.name)
    
    return repo.html_url
