export interface ExternalIdentityLookup {
  findUserIdByExternalIdentity(provider: string, subject: string): string | null;
}
