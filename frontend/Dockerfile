# ---------------------------------------------------------
# Dockerfile - DevOps Blog (static site served by Nginx)
# ---------------------------------------------------------
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy custom nginx config (optional, gzip + caching tweaks)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static site into nginx html directory
COPY website/ /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
