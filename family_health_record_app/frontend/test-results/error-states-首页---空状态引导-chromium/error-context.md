# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e6] [cursor=pointer]:
    - button "Open Next.js Dev Tools" [ref=e7]:
      - img [ref=e8]
    - generic [ref=e11]:
      - button "Open issues overlay" [ref=e12]:
        - generic [ref=e13]:
          - generic [ref=e14]: "1"
          - generic [ref=e15]: "2"
        - generic [ref=e16]:
          - text: Issue
          - generic [ref=e17]: s
      - button "Collapse issues badge" [ref=e18]:
        - img [ref=e19]
  - alert [ref=e21]
  - main [ref=e22]:
    - generic [ref=e23]:
      - img [ref=e25]
      - generic [ref=e27]:
        - heading "服务连接异常" [level=1] [ref=e28]
        - paragraph [ref=e29]: 网络连接失败，请确认后端 API 是否在 8000 端口运行
      - button "重试连接" [ref=e30] [cursor=pointer]:
        - img [ref=e31]
        - generic [ref=e34]: 重试连接
```