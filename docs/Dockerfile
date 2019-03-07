FROM python:3.6-slim as builder
COPY  docs /build/docs
COPY mkdocs.yml /build/mkdocs.yml
WORKDIR build
RUN pip install mkdocs \
    &&  mkdocs build

FROM nginx:latest
RUN rm -rf /etc/nginx/conf.d
COPY nginx/nginx.conf etc/nginx/conf.d/nginx.conf
COPY --from=builder /build/site /static/
EXPOSE 80
EXPOSE 443