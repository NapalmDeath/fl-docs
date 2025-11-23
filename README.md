# Diplodoc Static Template

### Confgure GitHub Pages

Enable GitHub pages (Settings -> Pages -> Build and deployment (Source) -> GitHub Action), then your github action will start working

### Local run

```sh
rm -rf ./build
npx -y @diplodoc/cli -i ./ -o ./build
npx -y http-server ./build --port=5000 --host=0.0.0.0 --cors
```

After that, just open http://localhost:5000

### Docker

If you need to build docker, just run the code

```sh
rm -rf ./build ./_site
npx -y @diplodoc/cli -i ./ -o ./_site
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t MYCOMPANY/docs .
docker push MYCOMPANY/docs:latest
```

### GitHub Docker build Action

Add the following secrets into the secret storage

```
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

Add the following steps into `.github/workflows/build.yml`

```yaml
      -
        name: Set up QEMU
        uses: docker/setup-qemu-action@v3
      -
        name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      -
        name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      -
        name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: MYCOMPANY/docs:latest
```

