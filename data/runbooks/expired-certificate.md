# Expired TLS certificate

Clients may reject connections and report certificate expiry or TLS handshake errors. Check the certificate's validity window and the served certificate chain. Confirm renewal and reload status before proposing certificate replacement; do not treat unrelated DNS errors as proof of expiry.
