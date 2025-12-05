# SSL Certificates Placeholder

This directory should contain your SSL certificates for HTTPS support.

## To use SSL certificates:

1. Place your certificate file as `cert.pem`
2. Place your private key file as `key.pem`

## Obtaining SSL certificates:

### Option 1: Let's Encrypt (Recommended for production)

```bash
docker run -it --rm -v /path/to/certs:/etc/letsencrypt certbot/certbot certonly --standalone -d yourdomain.com
```

### Option 2: Self-signed certificate (For development only)

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Then copy the generated files to this directory and uncomment the HTTPS configuration in `nginx.conf`.

## Important Security Notes:

- Keep private keys secure and never commit to version control
- Use proper certificates in production (Let's Encrypt, paid SSL, etc.)
- Self-signed certificates are only for development/testing
