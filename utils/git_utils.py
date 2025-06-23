import logging
import os
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# import nest_asyncio  # Added import
from git import Repo

# nest_asyncio.apply()  # Added call


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Base exception class for GitHub utility errors."""
    pass


# File extensions to skip during repository analysis
SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip',
    '.jar', '.class', '.pyc', '.exe', '.dll', '.so',
    '.md', '.json', '.xml', '.txt'
}

# Programming language detection mapping
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'React/JSX',
    '.tsx': 'React/TSX',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.go': 'Go',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.r': 'R',
    '.m': 'Objective-C/MATLAB',
    '.pl': 'Perl',
    '.sh': 'Shell/Bash',
    '.bash': 'Bash',
    '.zsh': 'Zsh',
    '.fish': 'Fish',
    '.ps1': 'PowerShell',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.vue': 'Vue.js',
    '.dart': 'Dart',
    '.lua': 'Lua',
    '.vim': 'Vim Script',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.conf': 'Config',
    '.dockerfile': 'Dockerfile',
}


class GitUtils:
    def validate_git_url(self, git_url: str) -> bool:
        """
        Validate Git repository URL for security.

        Args:
            git_url: URL to validate

        Returns:
            bool: Whether the URL is valid
        """
        try:
            result = urlparse(git_url)
            # Check for valid schemes and basic structure
            return all([
                result.scheme in ['https', 'git', 'ssh'],
                result.netloc,  # Ensure there's a domain
                any(domain in result.netloc for domain in ['github.com', 'gitlab.com', 'bitbucket.org'])
            ])
        except Exception:
            return False

    def clone_repository(self, git_url: str, branch: str = "main") -> str:
        """
        Clone the specified git repository.

        Args:
            git_url: Git repository URL
            branch: Branch to checkout (default: main)

        Returns:
            str: Path to the cloned repository

        Raises:
            GitHubError: If cloning fails
        """

        # Validate URL first
        if not self.validate_git_url(git_url):
            raise GitHubError("Invalid or potentially malicious repository URL")

        temp_dir = tempfile.mkdtemp()
        logger.info(f"Cloning {git_url} (branch: {branch}) to {temp_dir}...")

        try:
            # Use GitPython to clone the repository
            masked_url = re.sub(r'://.*@', '://[REDACTED]@', git_url)
            logger.info(f"Cloning repository (branch: {branch})...")

            repo = Repo.clone_from(git_url, temp_dir)

            # Try to checkout the specified branch, fallback to master if main doesn't exist
            try:
                repo.git.checkout(branch)
            except Exception:
                if branch == "main":
                    try:
                        repo.git.checkout("master")
                        logger.info("Branch 'main' not found, checked out 'master' instead")
                    except Exception:
                        logger.info("Using default branch")
                else:
                    raise

            logger.info(f"Successfully cloned repository to {temp_dir}")
            return temp_dir
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Error cloning repository: {str(e)}")
            raise GitHubError("Repository cloning failed. Please check the URL and try again.") from e

    def get_file_list_helper(self, repo_path: str) -> List[str]:
        """
        Helper function to get list of files in the repository, excluding binary and hidden files.

        Args:
            repo_path: Path to repository

        Returns:
            list: List of file paths relative to repository root
        """
        file_list = []
        repo_path = Path(repo_path)

        try:
            for path in repo_path.rglob('*'):
                # Skip directories
                if path.is_dir():
                    continue

                # Skip .git directory
                if '.git' in path.parts:
                    continue

                # Skip hidden directories and files
                if any(part.startswith('.') for part in path.parts):
                    continue

                # Skip __pycache__ and similar directories
                if any(part.startswith('__') for part in path.parts):
                    continue

                # Skip files with extensions we want to ignore
                if path.suffix.lower() in SKIP_EXTENSIONS:
                    continue

                # Add relative path to the list
                rel_path = str(path.relative_to(repo_path))
                file_list.append(rel_path)

            return file_list
        except Exception as e:
            logger.error(f"Error getting file list: {str(e)}")
            return []

    def get_git_stats(self, repo_path: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the Git repository.

        Args:
            repo_path: Path to the Git repository

        Returns:
            dict: Repository statistics including commits, contributors, branches, etc.
        """
        try:
            repo = Repo(repo_path)
            stats = {}

            # Basic repository info
            stats['repository_path'] = repo_path
            stats['current_branch'] = repo.active_branch.name
            stats['remote_url'] = list(repo.remotes.origin.urls)[0] if repo.remotes else None

            # Branch information
            stats['total_branches'] = len(list(repo.branches))
            stats['branch_names'] = [branch.name for branch in repo.branches]

            # Remote branches
            try:
                remote_branches = [ref.name.split('/')[-1] for ref in repo.remote().refs if 'HEAD' not in ref.name]
                stats['remote_branches'] = remote_branches
                stats['total_remote_branches'] = len(remote_branches)
            except Exception:
                stats['remote_branches'] = []
                stats['total_remote_branches'] = 0

            # Commit statistics
            commits = list(repo.iter_commits())
            stats['total_commits'] = len(commits)

            if commits:
                # First and last commit dates
                stats['first_commit_date'] = commits[-1].committed_datetime.isoformat()
                stats['last_commit_date'] = commits[0].committed_datetime.isoformat()

                # Repository age in days
                first_commit = commits[-1].committed_datetime
                last_commit = commits[0].committed_datetime
                stats['repository_age_days'] = (last_commit - first_commit).days

            # Contributors
            contributors = set()
            for commit in commits:
                contributors.add(commit.author.email)
            stats['total_contributors'] = len(contributors)
            stats['contributors'] = list(contributors)

            # Tags
            tags = list(repo.tags)
            stats['total_tags'] = len(tags)
            stats['tag_names'] = [tag.name for tag in tags]

            # File statistics
            file_list = self.get_file_list_helper(repo_path)
            stats['total_files'] = len(file_list)

            return stats

        except Exception as e:
            logger.error(f"Error getting git stats: {str(e)}")
            raise GitHubError(f"Failed to get git stats: {str(e)}") from e

    def get_commit_history(self, repo_path: str, limit: int = 20, since_days: Optional[int] = None) -> List[
        Dict[str, Any]]:
        """
        Get commit history with detailed information.

        Args:
            repo_path: Path to the Git repository
            limit: Maximum number of commits to return
            since_days: Only return commits from the last N days

        Returns:
            list: List of commit information dictionaries
        """
        try:
            repo = Repo(repo_path)
            commits = []

            # Calculate since date if specified
            since_date = None
            if since_days:
                since_date = datetime.now() - timedelta(days=since_days)

            commit_iter = repo.iter_commits()
            count = 0

            for commit in commit_iter:
                if count >= limit:
                    break

                commit_date = datetime.fromtimestamp(commit.committed_date)

                # Skip commits older than since_date if specified
                if since_date and commit_date < since_date:
                    continue

                commit_info = {
                    'hash': commit.hexsha,
                    'short_hash': commit.hexsha[:7],
                    'message': commit.message.strip(),
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'committed_date': commit_date.isoformat(),
                    'files_changed': len(commit.stats.files),
                    'insertions': commit.stats.total['insertions'],
                    'deletions': commit.stats.total['deletions'],
                    'changed_files': list(commit.stats.files.keys())
                }

                commits.append(commit_info)
                count += 1

            return commits

        except Exception as e:
            logger.error(f"Error getting commit history: {str(e)}")
            raise GitHubError(f"Failed to get commit history: {str(e)}") from e

    def identify_programming_languages(self, repo_path: str) -> Dict[str, Any]:
        """
        Identify programming languages used in the repository.

        Args:
            repo_path: Path to the Git repository

        Returns:
            dict: Language statistics and breakdown
        """
        try:
            file_list = self.get_file_list_helper(repo_path)
            language_stats = Counter()
            file_count = Counter()

            for file_path in file_list:
                file_path_obj = Path(file_path)
                extension = file_path_obj.suffix.lower()

                if extension in LANGUAGE_EXTENSIONS:
                    language = LANGUAGE_EXTENSIONS[extension]
                    language_stats[language] += 1
                    file_count[extension] += 1

            # Calculate percentages
            total_files = sum(language_stats.values())
            language_percentages = {}

            if total_files > 0:
                for language, count in language_stats.items():
                    language_percentages[language] = {
                        'files': count,
                        'percentage': round((count / total_files) * 100, 2)
                    }

            # Sort by file count
            sorted_languages = dict(sorted(language_percentages.items(),
                                           key=lambda x: x[1]['files'], reverse=True))

            result = {
                'total_code_files': total_files,
                'languages': sorted_languages,
                'primary_language': max(language_stats, key=language_stats.get) if language_stats else None,
                'extension_breakdown': dict(file_count)
            }

            return result

        except Exception as e:
            logger.error(f"Error identifying programming languages: {str(e)}")
            raise GitHubError(f"Failed to identify programming languages: {str(e)}") from e

    def get_repository_structure(self, repo_path: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get the directory structure of the repository.

        Args:
            repo_path: Path to the Git repository
            max_depth: Maximum depth to traverse

        Returns:
            dict: Repository structure information
        """
        try:
            repo_path_obj = Path(repo_path)
            structure = {}

            def build_tree(path: Path, current_depth: int = 0) -> Dict:
                if current_depth > max_depth:
                    return {}

                tree = {}
                try:
                    for item in sorted(path.iterdir()):
                        # Skip .git directory
                        if item.name == '.git':
                            continue

                        # Skip hidden files/directories
                        if item.name.startswith('.'):
                            continue

                        if item.is_dir():
                            tree[item.name + '/'] = build_tree(item, current_depth + 1)
                        else:
                            # Skip binary files
                            if item.suffix.lower() not in SKIP_EXTENSIONS:
                                tree[item.name] = 'file'

                except PermissionError:
                    pass

                return tree

            structure = build_tree(repo_path_obj)

            # Count directories and files
            def count_items(tree_dict):
                files = 0
                dirs = 0
                for key, value in tree_dict.items():
                    if key.endswith('/'):
                        dirs += 1
                        sub_files, sub_dirs = count_items(value)
                        files += sub_files
                        dirs += sub_dirs
                    else:
                        files += 1
                return files, dirs

            total_files, total_dirs = count_items(structure)

            result = {
                'structure': structure,
                'total_directories': total_dirs,
                'total_files': total_files,
                'max_depth_shown': max_depth
            }

            return result

        except Exception as e:
            logger.error(f"Error getting repository structure: {str(e)}")
            raise GitHubError(f"Failed to get repository structure: {str(e)}") from e

    def get_contributor_stats(self, repo_path: str) -> Dict[str, Any]:
        """
        Get detailed contributor statistics.

        Args:
            repo_path: Path to the Git repository

        Returns:
            dict: Contributor statistics
        """
        try:
            repo = Repo(repo_path)
            contributor_stats = defaultdict(lambda: {
                'commits': 0,
                'insertions': 0,
                'deletions': 0,
                'first_commit': None,
                'last_commit': None,
                'files_changed': set()
            })

            for commit in repo.iter_commits():
                author = commit.author.email
                stats = contributor_stats[author]

                stats['commits'] += 1
                stats['insertions'] += commit.stats.total['insertions']
                stats['deletions'] += commit.stats.total['deletions']
                stats['files_changed'].update(commit.stats.files.keys())

                commit_date = datetime.fromtimestamp(commit.committed_date)
                if stats['first_commit'] is None or commit_date < stats['first_commit']:
                    stats['first_commit'] = commit_date
                if stats['last_commit'] is None or commit_date > stats['last_commit']:
                    stats['last_commit'] = commit_date

                # Store author name for the first time we see this email
                if 'name' not in stats:
                    stats['name'] = commit.author.name

            # Convert to regular dict and format dates
            result = {}
            for email, stats in contributor_stats.items():
                result[email] = {
                    'name': stats['name'],
                    'commits': stats['commits'],
                    'insertions': stats['insertions'],
                    'deletions': stats['deletions'],
                    'files_changed': len(stats['files_changed']),
                    'first_commit': stats['first_commit'].isoformat() if stats['first_commit'] else None,
                    'last_commit': stats['last_commit'].isoformat() if stats['last_commit'] else None,
                    'total_changes': stats['insertions'] + stats['deletions']
                }

            # Sort by number of commits
            sorted_contributors = dict(sorted(result.items(),
                                              key=lambda x: x[1]['commits'], reverse=True))

            return {
                'contributors': sorted_contributors,
                'total_contributors': len(sorted_contributors)
            }

        except Exception as e:
            logger.error(f"Error getting contributor stats: {str(e)}")
            raise GitHubError(f"Failed to get contributor stats: {str(e)}") from e

    def search_commits(self, repo_path: str, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search commits by message content.

        Args:
            repo_path: Path to the Git repository
            search_term: Term to search for in commit messages
            limit: Maximum number of results to return

        Returns:
            list: List of matching commits
        """
        try:
            repo = Repo(repo_path)
            matching_commits = []

            for commit in repo.iter_commits():
                if len(matching_commits) >= limit:
                    break

                if search_term.lower() in commit.message.lower():
                    commit_info = {
                        'hash': commit.hexsha,
                        'short_hash': commit.hexsha[:7],
                        'message': commit.message.strip(),
                        'author_name': commit.author.name,
                        'author_email': commit.author.email,
                        'committed_date': datetime.fromtimestamp(commit.committed_date).isoformat(),
                        'files_changed': len(commit.stats.files)
                    }
                    matching_commits.append(commit_info)

            return matching_commits

        except Exception as e:
            logger.error(f"Error searching commits: {str(e)}")
            raise GitHubError(f"Failed to search commits: {str(e)}") from e

    def cleanup_repository(self, repo_path: str) -> bool:
        """
        Clean up the cloned repository by removing the temporary directory.

        Args:
            repo_path: Path to the repository to clean up

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Additional safety checks before deletion
            if not repo_path or not os.path.isabs(repo_path):
                logger.warning("Invalid repository path for cleanup")
                return False

            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info(f"Successfully cleaned up repository at {repo_path}")
                return True
            else:
                logger.warning(f"Repository path does not exist: {repo_path}")
                return False
        except Exception as e:
            logger.error(f"Error cleaning up repository: {str(e)}")
            return False
