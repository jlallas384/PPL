FROM node:24-alpine AS build
WORKDIR /app
COPY ./web/frontend .
RUN npm i && npm run build

FROM python:3
RUN apt-get update && apt-get install -y nginx gettext
COPY --from=build /app/dist /usr/share/nginx/html

WORKDIR /app
COPY compiler compiler
COPY web web
RUN pip install --no-cache-dir -r ./compiler/requirements.txt && pip install --no-cache-dir -r ./web/backend/requirements.txt

COPY nginx.conf .

COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
