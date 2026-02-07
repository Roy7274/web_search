1安装项目依赖并运行

    > 说明
    >
    > 默认在 localhost:8888 提供符合 openAI 规范的 chatAPI 服务

    ```shell
    python -m venv .venv
    source .venv/bin/activate
        
    poetry install
    poetry run python -m server
    ```

2. 启动webui

    ```shell
    # 在项目根目录的 .env 中填写 API_ADDR（连接本地 server 时填 http://localhost:8888/api/v3/bots）
    
    python -m venv .venv
    source .venv/bin/activate
    poetry install
    
    # 启动web ui
    poetry run python -m webui
    ```
3. 使用浏览器访问 `http://localhost:7860/` 即可使用