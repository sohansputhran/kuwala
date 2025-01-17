import h3
import math

import asyncio
import src.utils.google as google
from config.h3.h3_config import POI_RESOLUTION
from quart import abort, Blueprint, jsonify, request
from src.utils.array_utils import get_nested_value

search = Blueprint('search', __name__)


@search.route('/search', methods=['GET'])
async def search_places():
    """Retrieve placeIDs for an array of query strings"""
    queries = await request.get_json()

    if len(queries) > 100:
        abort(400, description='You can send at most 100 queries at once.')

    loop = asyncio.get_event_loop()

    def parse_result(r):
        data = r['data']
        lat = round(get_nested_value(data, 9, 2), 7)  # 7 digits equals a precision of 1 cm
        lng = round(get_nested_value(data, 9, 3), 7)  # 7 digits equals a precision of 1 cm
        # noinspection PyUnresolvedReferences
        h3_index = h3.geo_to_h3(lat, lng, POI_RESOLUTION)
        pb_id = get_nested_value(data, 10)

        return dict(
            query=r['query'],
            data=dict(
                location=dict(lat=lat, lng=lng),
                h3Index=h3_index,
                id=pb_id
            )
        )

    futures = []
    for query in queries:
        futures.append(loop.run_in_executor(None, google.search, query))

    results = loop.run_until_complete(asyncio.gather(*futures))
    
    parsed = []
    for result in results:
        parsed.append(parse_result(result))


    return jsonify({'success': True, 'data': parsed})
