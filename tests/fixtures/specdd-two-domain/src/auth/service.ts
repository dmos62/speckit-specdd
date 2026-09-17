import type { ExternalIdentityLookup } from "../users/identity-contract";

export class AuthService {
  constructor(private readonly identities: ExternalIdentityLookup) {}

  resolveUserId(provider: string, subject: string): string | null {
    return this.identities.findUserIdByExternalIdentity(provider, subject);
  }
}
