
# v2subs

generate v2ray/v2fly subscription file using server JSON config file



## how to use

two files should be provided:

 1. **config.json**
	this is the main config file of v2ray server. v2subs reads inbound data from this file to generate subscription data.
	v2subs currently supports ws/grpc transports + vmess/trojan protocols
2. **domain-map.json**
	this file maps inbound tag to ip or url pointing to each one as follow:
	```yaml
		{
		  "inbound-1-tag": [
            {
            "target": "ip:port",
            "sni":"example.com", # if ip is provided as target, profile wouldn't set tls, unless sni provided
            "tag": "tls profile 1" # optional label to show on client profile
            }
        ],
        "inbound-2-tag": [
            {  	# if provided target domain scheme is http, connection wouldn't set tls, unless sni provided
            "target": "http://domain:port",
            "sni":"sni.example.com",
            "tag": "tls profile 2"
            },
            {
            "target": "http://domain:port",
            "tag": "http profile 1"
            },
            { 	# multiple front-ends can be set for each inbound
            "target": "https://example.com:8181",
            # if provided target domain scheme is https, sni is optional
            "tag": "tls profile 3"
            }
        ]
        }
	```
