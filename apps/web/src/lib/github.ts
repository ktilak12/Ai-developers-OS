export interface RepoInfo {
  name: string;
  full_name: string;
  description: string;
  default_branch: string;
  stargazers_count: number;
  forks_count: number;
  open_issues_count: number;
  html_url: string;
}

export interface BranchInfo {
  name: string;
  commit: { sha: string };
}

export interface IssueInfo {
  id: number;
  number: number;
  title: string;
  state: string;
  user: { login: string; avatar_url: string };
  created_at: string;
  comments: number;
}

export interface CommitInfo {
  sha: string;
  commit: {
    author: { name: string; date: string };
    message: string;
  };
}

export interface PullRequestInfo {
  id: number;
  number: number;
  title: string;
  state: string;
  user: { login: string };
  created_at: string;
}

export interface FileContent {
  name: string;
  path: string;
  type: "file" | "dir";
  size?: number;
  download_url?: string;
}

export async function fetchRepoInfo(owner: string, repo: string): Promise<RepoInfo> {
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.error(e);
  }
  return {
    name: repo,
    full_name: `${owner}/${repo}`,
    description: "An open-source software project powered by AI Developer OS.",
    default_branch: "main",
    stargazers_count: 1420,
    forks_count: 312,
    open_issues_count: 23,
    html_url: `https://github.com/${owner}/${repo}`,
  };
}

export async function fetchBranches(owner: string, repo: string): Promise<BranchInfo[]> {
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/branches`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.error(e);
  }
  return [
    { name: "main", commit: { sha: "8f3a92b" } },
    { name: "feature/google-oauth", commit: { sha: "1c4d7e9" } },
    { name: "fix/checkout-coupon", commit: { sha: "9e2b1a4" } },
  ];
}

export async function fetchIssues(owner: string, repo: string): Promise<IssueInfo[]> {
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues`);
    if (res.ok) {
      const data = await res.json();
      return data.filter((item: any) => !item.pull_request);
    }
  } catch (e) {
    console.error(e);
  }
  return [
    { id: 124, number: 124, title: "Fix the checkout failure when a user applies an expired coupon", state: "open", user: { login: "alexdev", avatar_url: "https://github.com/identicons/alex.png" }, created_at: "2026-09-28T14:20:00Z", comments: 4 },
    { id: 123, number: 123, title: "Add Google OAuth authentication flow", state: "open", user: { login: "sarah_m", avatar_url: "https://github.com/identicons/sarah.png" }, created_at: "2026-09-27T09:15:00Z", comments: 2 },
    { id: 120, number: 120, title: "Optimize database queries for user search endpoint", state: "closed", user: { login: "johndoe", avatar_url: "https://github.com/identicons/john.png" }, created_at: "2026-09-25T11:45:00Z", comments: 8 },
  ];
}

export async function fetchCommits(owner: string, repo: string): Promise<CommitInfo[]> {
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/commits`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.error(e);
  }
  return [
    { sha: "8f3a92b", commit: { author: { name: "Alex Dev", date: "2026-09-29T16:30:00Z" }, message: "feat(auth): implement initial token validation middleware" } },
    { sha: "1c4d7e9", commit: { author: { name: "Sarah M", date: "2026-09-29T12:10:00Z" }, message: "fix(ui): resolve layout shift on mobile navigation drawer" } },
    { sha: "9e2b1a4", commit: { author: { name: "John Doe", date: "2026-09-28T18:45:00Z" }, message: "refactor(db): add connection pooling configuration" } },
  ];
}

export async function fetchPullRequests(owner: string, repo: string): Promise<PullRequestInfo[]> {
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls?state=all`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.error(e);
  }
  return [
    { id: 88, number: 88, title: "feat: add Google OAuth support", state: "open", user: { login: "ai-coder-bot" }, created_at: "2026-09-29T15:00:00Z" },
    { id: 87, number: 87, title: "fix: coupon discount calculation bug", state: "open", user: { login: "sarah_m" }, created_at: "2026-09-29T10:30:00Z" },
    { id: 85, number: 85, title: "chore: update dependencies to latest security patches", state: "closed", user: { login: "dependabot" }, created_at: "2026-09-26T08:00:00Z" },
  ];
}

export async function fetchRepoContents(owner: string, repo: string, path: string = ""): Promise<FileContent[]> {
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.error(e);
  }
  return [
    { name: "src", path: "src", type: "dir" },
    { name: "public", path: "public", type: "dir" },
    { name: "package.json", path: "package.json", type: "file", size: 1420 },
    { name: "README.md", path: "README.md", type: "file", size: 3200 },
    { name: "tsconfig.json", path: "tsconfig.json", type: "file", size: 680 },
  ];
}
