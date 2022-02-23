import hashlib
import logging
import cbor

from pprint import pprint
from io import BufferedReader

import asyncclick as click

from mcumgr import smp
from mcumgr.smp_ble import SMPBLEClient

from bleak import BleakScanner

logger = logging.getLogger(__name__)


@click.group()
@click.option('--ble-address')
@click.pass_context
async def cli(ctx, **kwargs):
    if ctx.invoked_subcommand != "ble" and kwargs['ble_address'] is not None:
        client = SMPBLEClient(address=kwargs['ble_address'])
        await client.connect()
        ctx.obj = client


@click.group()
async def ble(**kwargs):
    pass


@click.command()
async def scan():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)


ble.add_command(scan)
cli.add_command(ble)


@click.group()
async def os(**kwargs):
    pass


@click.command()
@click.pass_obj
async def reset(obj: SMPBLEClient):
    req = smp.MgmtMsg()
    req.hdr.nh_op = smp.MGMT_OP.WRITE
    req.hdr.nh_group = smp.MGMT_GROUP_ID.OS
    req.hdr.nh_id = smp.Mynewt.OS_MGMT_ID.RESET
    req.set_payload(cbor.dumps({}))

    response = await obj.send_request(req)
    pprint(cbor.loads(response.payload))

    await obj.disconnect()


@click.command()
@click.argument('msg')
@click.pass_obj
async def echo(obj: SMPBLEClient, msg):
    req = smp.MgmtMsg()
    req.hdr.nh_op = smp.MGMT_OP.WRITE
    req.hdr.nh_group = smp.MGMT_GROUP_ID.OS
    req.hdr.nh_id = smp.Mynewt.OS_MGMT_ID.ECHO
    data = cbor.dumps({"d": msg})
    req.set_payload(data)

    response = await obj.send_request(req)
    pprint(cbor.loads(response.payload))

    await obj.disconnect()


os.add_command(reset)
os.add_command(echo)
cli.add_command(os)


@click.group()
async def image(**kwargs):
    pass


@click.command()
@click.pass_obj
async def list(obj: SMPBLEClient):
    req = smp.MgmtMsg()
    req.hdr.nh_op = smp.MGMT_OP.READ
    req.hdr.nh_group = smp.MGMT_GROUP_ID.IMAGE
    req.hdr.nh_id = smp.Mynewt.IMAGE_MGMT_ID.STATE
    data = cbor.dumps({})
    req.set_payload(data)

    response = await obj.send_request(req)
    payload = cbor.loads(response.payload)
    click.echo(f"Images (split status): {payload['splitStatus']}:")
    for image in payload['images']:
        flags = ['bootable', 'pending', 'confirmed', 'active', 'permanent']

        str_flags = ", ".join([flag for flag in flags if image[flag]])

        click.echo(f"  slot: {image['slot']}")
        click.echo(f"  hash: {image['hash'].hex()}")
        click.echo(f"  version: {image['version']}")
        click.echo("  flags: {}".format(str_flags))
        click.echo("")

    await obj.disconnect()


@click.command()
@click.argument('input', type=click.File('rb'))
@click.pass_obj
async def upload(obj: SMPBLEClient, input: BufferedReader):
    req = smp.MgmtMsg()
    req.hdr.nh_op = smp.MGMT_OP.WRITE
    req.hdr.nh_group = smp.MGMT_GROUP_ID.IMAGE
    req.hdr.nh_id = smp.Mynewt.IMAGE_MGMT_ID.UPLOAD

    image = input.read()
    m = hashlib.sha256()
    m.update(image)
    hash = m.digest()
    logger.debug(f"hash: {hash}")

    chunk_size = 165
    logger.debug(f"chunk size: {chunk_size}")
    for i in range(0, len(image), chunk_size):
        chunk = image[i:i + chunk_size]

        data = cbor.dumps({
            "data": chunk,
            "len": len(image),
            "off": i,
            "sha": hash
        })
        req.set_payload(data)

        print(f'{i}/{len(image)}')
        response = await obj.send_request(req)

    await obj.disconnect()


@click.command()
@click.argument('hash')
@click.pass_obj
async def test(obj: SMPBLEClient, hash):
    req = smp.MgmtMsg()
    req.hdr.nh_op = smp.MGMT_OP.WRITE
    req.hdr.nh_group = smp.MGMT_GROUP_ID.IMAGE
    req.hdr.nh_id = smp.Mynewt.IMAGE_MGMT_ID.STATE
    print(bytes.fromhex(hash))
    data = cbor.dumps({
        'hash': bytes.fromhex(hash),
        'confirm': False
    })
    req.set_payload(data)

    response = await obj.send_request(req)
    pprint(cbor.loads(response.payload))

    await obj.disconnect()


@click.command()
@click.argument('hash')
@click.pass_obj
async def confirm(obj: SMPBLEClient, hash):
    req = smp.MgmtMsg()
    req.hdr.nh_op = smp.MGMT_OP.WRITE
    req.hdr.nh_group = smp.MGMT_GROUP_ID.IMAGE
    req.hdr.nh_id = smp.Mynewt.IMAGE_MGMT_ID.STATE
    print(bytes.fromhex(hash))
    data = cbor.dumps({
        'hash': bytes.fromhex(hash),
        'confirm': True
    })
    req.set_payload(data)

    response = await obj.send_request(req)
    pprint(cbor.loads(response.payload))

    await obj.disconnect()


image.add_command(list)
image.add_command(upload)
image.add_command(test)
image.add_command(confirm)
cli.add_command(image)


def main():
    cli()


if __name__ == '__main__':
    main()
