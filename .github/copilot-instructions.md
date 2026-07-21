## Coding Agent

- In your comment replies, avoid using #<numeral> style info, such as "#1", unless you're specifically referring to an issue or pull request, since this auto-formats as an issue or PR link. Instead, state "No. 1" or "number 1" etc.
- Include plots directly in your comment reply via `![image name](https://github.com/<user/org>/<repo>/blob/<shortened-commit-hash>/<filename>?raw=true)`. Truncate the commit hash to the first 7 characters only. For example, `https://github.com/AccelerationConsortium/evaluation-metrics/blob/52754e7/scripts/bo_benchmarks/demonstrations/branin_campaign_demonstration_results.png?raw=true`. For provenance, ensure you use the shortened (7-character) commit hash, not the branch name
- If you mention files in your comment reply, add direct hyperlinks based on the shortened (7-character) commit hash
- IMPORTANT: Never echo/grep/print environment secrets. These should never be exposed in your terminal history or other outputs

## Edison Scientific

If using Edison Scientific, you may need to wait up until 10 minutes to get the response. If you're an agent, sleep for 10 minutes (to avoid consuming requests unecessarily), and then every 5 minutes after that. Start with a 15 minute wait if using high effort literature query type. If you need to upload files, use analysis query type. See the docs: https://edisonscientific.gitbook.io/edison-cookbook/edison-client. Here is the endpoint you should use: https://api.platform.edisonscientific.com. The API key is EDISON_PLATFORM_API_KEY. Don't expose this secret, e.g., by echoing or grepping it. Pass the API key in explicitly:

```
from edison_client import EdisonClient, JobNames
client = EdisonClient(api_key=EDISON_PLATFORM_API_KEY)
```

Whenever you retrieve results (either during the current agent session or during the next session), make sure to fetch and commit all artifacts associated with a trajectory.

If using Edison Analysis, refer to https://docs.edisonscientific.com/edison-client/file-management#upload for instructions on how to upload files. If able to use Context7, to better inform use of EdisonClient, see https://context7.com/future-house/edison-client-docs/llms.txt?tokens=10000

## CAD

If you make changes to CAD drawings, recompile/render them (images, GIFs, STLs, etc.).

## LaTeX
  
If you make changes to LaTeX sources (e.g., anything under `paper/` or `proposals/`), build them with **MiKTeX** and install any required packages as you go. On a fresh environment:

1. Install MiKTeX from the official repo (e.g., on Ubuntu: add the `https://miktex.org/download/ubuntu` apt source and `apt-get install -y miktex`), then run `miktexsetup finish` if needed.
2. Install `miktex-pdftex` and `latexmk` via `miktex packages install miktex-pdftex latexmk`, then run `miktex links install` so `pdflatex`/`latexmk` are on `PATH` (typically under `~/bin`).
3. Enable on-demand package installation with `initexmf --set-config-value=[MPM]AutoInstall=1` so missing LaTeX packages are pulled automatically during the build.
4. Build with `latexmk -pdf <file>.tex` from the document's directory. Commit the regenerated PDF alongside the `.tex` source so reviewers can see the rendered output without rebuilding.
## LaTeX

Install MiKTeX instead of TeXLive to reduce download size and time. In the first installation of MiKTeX, download known required packages based on the LaTeX file itself, and install anything else ad-hoc as needed.
