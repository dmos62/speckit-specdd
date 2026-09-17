import type { ExternalIdentityLookup } from "./identity-contract";

export class UsersRepository implements ExternalIdentityLookup {
  readonly #externalIdentities = new Map<string, string>();

  findUserIdByExternalIdentity(provider: string, subject: string): string | null {
    return this.#externalIdentities.get(`${provider}:${subject}`) ?? null;
  }

  linkExternalIdentity(provider: string, subject: string, userId: string): void {
    this.#externalIdentities.set(`${provider}:${subject}`, userId);
  }
}
