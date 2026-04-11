import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://docs.dockrion.io',
  integrations: [
    starlight({
      title: 'Dockrion',
      logo: {
        src: './src/assets/logo.svg',
        alt: 'Dockrion',
      },
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/paritosh0707/Dockrion' },
      ],
      defaultLocale: 'root',
      expressiveCode: {
        themes: ['dracula'],
        styleOverrides: {
          borderRadius: '8px',
        },
      },
      sidebar: [
        {
          label: 'Introduction',
          items: [
            { label: 'Overview', slug: 'introduction' },
            { label: 'What is Dockrion', slug: 'introduction/what-is-dockrion' },
            { label: 'Core Concepts', slug: 'introduction/core-concepts' },
            { label: 'Architecture Overview', slug: 'introduction/architecture-overview' },
            { label: 'Quickstart', slug: 'introduction/quickstart' },
            { label: 'Roadmap', slug: 'introduction/roadmap' },
          ],
        },
        {
          label: 'The Dockfile',
          items: [
            { label: 'Overview', slug: 'the-dockfile' },
            { label: 'Agent', slug: 'the-dockfile/agent' },
            { label: 'IO Schema', slug: 'the-dockfile/io-schema' },
            { label: 'Metadata', slug: 'the-dockfile/metadata' },
            { label: 'Build Config', slug: 'the-dockfile/build-config' },
            { label: 'Env Substitution', slug: 'the-dockfile/env-substitution' },
            { label: 'Secrets', slug: 'the-dockfile/secrets' },
            { label: 'Observability', slug: 'the-dockfile/observability' },
            { label: 'Complete Example', slug: 'the-dockfile/complete-example' },
            {
              label: 'Authentication',
              items: [
                { label: 'Overview', slug: 'the-dockfile/auth' },
                { label: 'API Key', slug: 'the-dockfile/auth/api-key' },
                { label: 'JWT', slug: 'the-dockfile/auth/jwt' },
                { label: 'OAuth2', slug: 'the-dockfile/auth/oauth2' },
                { label: 'Roles & Rate Limits', slug: 'the-dockfile/auth/roles-and-rate-limits' },
              ],
            },
            {
              label: 'Policies',
              items: [
                { label: 'Overview', slug: 'the-dockfile/policies' },
                { label: 'Prompt Injection', slug: 'the-dockfile/policies/prompt-injection' },
                { label: 'Output Controls', slug: 'the-dockfile/policies/output-controls' },
                { label: 'Tool Gating', slug: 'the-dockfile/policies/tool-gating' },
              ],
            },
            {
              label: 'Streaming',
              items: [
                { label: 'Overview', slug: 'the-dockfile/streaming' },
                { label: 'SSE', slug: 'the-dockfile/streaming/sse' },
                { label: 'Async Runs', slug: 'the-dockfile/streaming/async-runs' },
                { label: 'Backends', slug: 'the-dockfile/streaming/backends' },
                { label: 'Event Types', slug: 'the-dockfile/streaming/event-types' },
                { label: 'Stream Context', slug: 'the-dockfile/streaming/stream-context' },
              ],
            },
          ],
        },
        {
          label: 'CLI Reference',
          items: [
            { label: 'Overview', slug: 'cli-reference' },
            { label: 'Core Commands', slug: 'cli-reference/core-commands' },
            { label: 'Utility Commands', slug: 'cli-reference/utility-commands' },
            { label: 'Exit Codes', slug: 'cli-reference/exit-codes' },
          ],
        },
        {
          label: 'The Generated API',
          items: [
            { label: 'Overview', slug: 'the-generated-api' },
            { label: 'Endpoints Reference', slug: 'the-generated-api/endpoints-reference' },
            { label: 'Auth (Caller\'s Perspective)', slug: 'the-generated-api/auth-callers-perspective' },
            { label: 'IO Schema & Swagger', slug: 'the-generated-api/io-schema-and-swagger' },
            { label: 'Streaming Consumption', slug: 'the-generated-api/streaming-consumption' },
          ],
        },
        {
          label: 'Guides & Recipes',
          items: [
            { label: 'Overview', slug: 'guides-and-recipes' },
            { label: 'Installation', slug: 'guides-and-recipes/installation' },
            { label: 'Adding Auth', slug: 'guides-and-recipes/adding-auth' },
            { label: 'Adding Policies', slug: 'guides-and-recipes/adding-policies' },
            { label: 'Adding Streaming', slug: 'guides-and-recipes/adding-streaming' },
            { label: 'Environment & Secrets', slug: 'guides-and-recipes/environment-and-secrets' },
            { label: 'Docker Build & Deployment', slug: 'guides-and-recipes/docker-build-and-deployment' },
            { label: 'Cloud Deployment', slug: 'guides-and-recipes/cloud-deployment' },
            { label: 'Invoice Copilot Walkthrough', slug: 'guides-and-recipes/invoice-copilot-walkthrough' },
            { label: 'Troubleshooting', slug: 'guides-and-recipes/troubleshooting' },
            { label: 'FAQ', slug: 'guides-and-recipes/faq' },
          ],
        },
        {
          label: 'Appendix',
          items: [
            { label: 'Overview', slug: 'appendix' },
            { label: 'Adapters Reference', slug: 'appendix/adapters-reference' },
            { label: 'Error Hierarchy', slug: 'appendix/error-hierarchy' },
            { label: 'SDK Reference', slug: 'appendix/sdk-reference' },
          ],
        },
      ],
    }),
  ],
});
