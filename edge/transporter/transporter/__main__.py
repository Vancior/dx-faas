from aiohttp import web
import aiohttp
import asyncio


async def handler(request):
    ip = request.match_info.get('ip')
    runtime_id = request.match_info.get('runtime_id')
    async with aiohttp.ClientSession() as session:
        body = await request.read()
        async with session.post(f'http://{ip}/{runtime_id}',
                headers={'Content-Type': 'application/json'},
                data=body) as response:
            content = await response.text()
            return web.Response(headers={'Content-Type': 'application/json'}, body=content)


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([web.post('/{ip}/{runtime_id}', handler)])

    web.run_app(app, port=6999)
