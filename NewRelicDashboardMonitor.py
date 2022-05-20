from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio

async def get_new_relic_response_time(apiKey, entityGuid)->dict:
	# Select your transport with a defined url endpoint
	transport = AIOHTTPTransport(url="https://api.newrelic.com/graphql",                          headers={'API-Key': apiKey})
	# Create a GraphQL client using the defined transport
	async with Client(transport=transport, fetch_schema_from_transport=True) as client:
		# Provide a GraphQL query
		query = gql(
			"""
			{{
			  actor {{
				entity(guid: "{entityGuid}") {{
				  nrdbQuery(nrql: "SELECT  percentile(duration, 95) * 1000 as response_duration from Transaction where transactionType = 'Web' and transactionSubType = 'SpringController' SINCE 15 minutes AGO") {{
				results
			  }}
			}}
		  }}
		}}
		""".format(entityGuid = entityGuid)
		)
		new_relic_result = await client.execute(query)

	return {"Service Response Time": new_relic_result.get("actor", {}).get("entity", {}).get("nrdbQuery", {}).get("results", [])[0].get("response_duration", 0)}
