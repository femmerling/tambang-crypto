# VipIo

VIP client optimized for performance and also an anti Cloudflare happy times included.

## Using

```python
from vipio from VipIo

url = 'https://vip.bitcoin.co.id/api/btc_idr/depth'

depths = VipIo.get_depths(['str_idr', 'btc_idr'], max_workers=20) # Public API with max 20 workers

vip = VipIo('API_KEY', 'API_SECRET')

info = vip.get_info() # Private API call
```