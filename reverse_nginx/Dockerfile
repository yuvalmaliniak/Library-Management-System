FROM nginx:latest

# Remove the default configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom NGINX configuration file to the expected location
COPY nginx.conf /etc/nginx/conf.d/default.conf
