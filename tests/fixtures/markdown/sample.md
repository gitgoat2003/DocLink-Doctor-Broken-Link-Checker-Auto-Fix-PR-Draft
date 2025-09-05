# Sample Test Document

This file contains various links for testing DocLink Doctor.

## Working Links

- [Working External Link](https://example.com)
- [Another Working Link](https://httpbin.org/status/200)

## Broken Links

- [Broken External Link](https://broken-example-404.com/notfound)
- [404 Error Link](https://httpbin.org/status/404)

## Internal Links

- [Local File](./existing-file.md)
- [Missing File](./missing-file.md)
- [Parent Directory](../README.md)

## Anchor Links

### Existing Section

Content here.

### Configuration Reference

More content.

- [Valid Anchor](#existing-section)
- [Missing Anchor](#nonexistent-anchor)
- [Another Missing](#header-three)

## Mixed Links

Check our [API docs](https://example-docs.com/v2/api) for more info.

Visit [localhost test](http://localhost:3000/api) during development.

<!-- doclink-ignore -->
[Ignored Link](https://should-be-ignored.com/page)
<!-- /doclink-ignore -->
