import { setupServer } from 'msw/node'

// Each test registers the API responses it needs with server.use(...); any request without
// a handler fails the test, so a page can never silently depend on an unmocked endpoint.
export const server = setupServer()
