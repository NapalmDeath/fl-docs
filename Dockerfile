FROM mhart/alpine-node

RUN npm install -g http-server

WORKDIR /site
ADD ./_site /site/docs

EXPOSE 5000

CMD ["http-server", "--port=5000", "--host=0.0.0.0", "--cors", " --log-ip", "/site/docs"]
