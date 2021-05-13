# ionos_dyndns.py

Create and update DNS records for a host using IONOS' API for use as a DynDNS (for example via a cronjob).
The script will create A and/or AAAA records if none already exists for the host and update existing ones to reflect the new public IP.

The public IP-Address is determined in two ways:

- **IPv4**: uses the **ipify.org** API
- **IPv6**: uses the `ip address show` command

By default the name of the A/AAAA record that will be created/updated is one that matches the output from the command `hostname -f`.<br>
Update your `/etc/hosts` file with your FQDN if it's not already there.<br>
Alternatively you can override this default value by using the `-H` or `--fqdn` parameter.

## Requirements

- Linux
- Python 3
- IONOS API key

You can create an API key here: https://developer.hosting.ionos.de/keys<br>
The API is still in Beta and not enabled by default. In my case I had to call the customer support hotline and request to be enabled for the API.

## Usage

### Cronjob

This example shows how to update the AAAA record every 5 minutes and save the script output to a file:

1. Download the script and make sure it is executable
```sh
wget https://raw.githubusercontent.com/lazaroblanc/IONOS-DynDNS/main/ionos_dyndns.py
chmod +x ionos_dyndns.py
```
2. Open your crontab file with `crontab -e`
3. Paste this line:
```sh
*/5 * * * * ./ionos_dyndns.py --AAAA --api-prefix $publicprefix --api-secret $secret >> ionos_dyndns.log
```

### General
```
usage: ionos_dyndns.py [-h] [-4] [-6] [-i] [-H] --api-prefix  --api-secret

Create and update DNS records for this host using IONOS' API to use as a sort of DynDNS (for example via a cronjob).

optional arguments:
  -h, --help         show this help message and exit
  -4, --A            Create/Update A record
  -6, --AAAA         Create/Update AAAA record
  -i , --interface   Interface name for determining the public IPv6 address (Default: eth0)
  -H , --fqdn        Host's FQDN (Default: hostname -f)
  --api-prefix       API key publicprefix
  --api-secret       API key secret
```

## Ideas / To-do

- [ ] improve log messages (add a timestamp)
- [ ] refactor duplicate code (~ line 94)

<div align="center">
<hr>
<table>
<tr>
<td colspan=2>
<h2>🐛 Bug reports & Feature requests 🆕</h2>
If you've found a bug or want to request a new feature please <a href="https://github.com/lazaroblanc/IONOS-DynDNS/issues/new">open a new <b>Issue</b></a>
<br><br>
</td>
</tr>
<tr>
<td>
<h2>🤝 Contributing</h2>
✅ Pull requests are welcome!
<br><br>
</td>
<td>
<h2>📃 License</h2>
Published under the <b>Apache License 2.0</b><br>
Please see the <a href="./LICENSE"><b>License</b></a> for details
<br><br>
</td>
</tr>
</table>
</div>
