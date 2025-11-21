## GitHub Copilot Chat

- Extension Version: 0.30.1 (prod)
- VS Code: vscode/1.103.1
- OS: Windows

## Network

User Settings:
```json
  "github.copilot.advanced.debug.useElectronFetcher": true,
  "github.copilot.advanced.debug.useNodeFetcher": false,
  "github.copilot.advanced.debug.useNodeFetchFetcher": true
```

Connecting to https://api.github.com:
- DNS ipv4 Lookup: 20.201.28.148 (9 ms)
- DNS ipv6 Lookup: Error (10 ms): getaddrinfo ENOTFOUND api.github.com
- Proxy URL: None (1 ms)
- Electron fetch (configured): HTTP 200 (87 ms)
- Node.js https: HTTP 200 (68 ms)
- Node.js fetch: HTTP 200 (81 ms)

Connecting to https://api.individual.githubcopilot.com/_ping:
- DNS ipv4 Lookup: 140.82.114.21 (9 ms)
- DNS ipv6 Lookup: Error (39 ms): getaddrinfo ENOTFOUND api.individual.githubcopilot.com
- Proxy URL: None (5 ms)
- Electron fetch (configured): HTTP 200 (137 ms)
- Node.js https: HTTP 200 (499 ms)
- Node.js fetch: HTTP 200 (426 ms)

## Documentation

In corporate networks: [Troubleshooting firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).