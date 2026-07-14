"""
Bulk Content Expander for AdSense Approval
Expands every article to 800+ words using deterministic content generation
based on the article's existing title, category, excerpt, key_takeaways, and FAQs.
"""
import json, re, os, hashlib

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_src', '_data')

def wc(html):
    return len(re.sub(r'<[^>]+>', ' ', html).split())

# Category-specific expansion templates
CATEGORY_SECTIONS = {
    "Equities": {
        "market_context": "The global equities market is valued at over $100 trillion, making it the largest asset class in the world. The tokenization of equity instruments represents a fundamental shift in how shares are issued, traded, and settled. Traditional equity markets rely on centralized clearinghouses like the DTCC in the United States, which process trillions of dollars in transactions daily but operate on legacy infrastructure that can take up to one business day (T+1) to fully settle a trade.",
        "investor_impact": "For retail investors, tokenized equities offer several transformative benefits. First, fractional ownership becomes natively supported — instead of needing thousands of dollars to buy a single share of a high-priced stock, investors can purchase tokens representing a fraction of a share for as little as $1. Second, 24/7 trading becomes possible since blockchain networks never close, unlike traditional stock exchanges that operate limited hours on weekdays only. Third, settlement is near-instantaneous, freeing up capital that would otherwise be locked during the T+1 settlement window.",
        "regulatory": "The regulatory landscape for tokenized equities is evolving rapidly. In the United States, the SEC has provided guidance through Regulation A+ (for public offerings up to $75 million) and Regulation D (for private placements to accredited investors). The European Union's Markets in Crypto-Assets (MiCA) regulation and the UK's Financial Conduct Authority (FCA) sandbox programs are also creating frameworks for compliant issuance. Issuers must maintain transfer agent records on-chain while meeting all applicable securities laws.",
        "risks": "Despite the promise, tokenized equities carry unique risks that investors must understand. Smart contract vulnerabilities could potentially compromise token integrity. Regulatory uncertainty means that rules could change, affecting the legality or tradability of tokens. Liquidity on secondary markets for security tokens remains significantly lower than traditional exchanges, which can lead to wider bid-ask spreads and difficulty exiting positions. Additionally, custody solutions for security tokens are still maturing compared to traditional brokerage accounts."
    },
    "Treasuries": {
        "market_context": "U.S. Treasury securities represent the bedrock of global finance, with over $33 trillion in outstanding debt as of 2024. These instruments are considered the safest investments in the world, backed by the full faith and credit of the United States government. The tokenization of treasury instruments brings this foundational asset class onto blockchain rails, enabling new forms of programmable finance and capital efficiency that were previously impossible.",
        "investor_impact": "For institutional and retail investors alike, tokenized treasuries offer compelling advantages. The ability to earn the risk-free rate while maintaining on-chain liquidity is a game-changer for DeFi protocols that previously relied entirely on volatile crypto assets for collateral. Tokenized treasuries can serve as pristine collateral in lending protocols, margin accounts, and structured products. The programmable nature of these tokens also enables automatic reinvestment of yields, real-time NAV calculations, and instant redemptions without the traditional T+1 settlement delay.",
        "regulatory": "Tokenized treasury products typically operate under strict regulatory frameworks. Issuers like BlackRock (BUIDL), Franklin Templeton (BENJI), and Ondo Finance (OUSG) register their products with the SEC and require comprehensive KYC/AML onboarding for all investors. The underlying treasuries are held by qualified custodians, and the tokens are issued as securities under existing regulations. This regulatory compliance, while limiting accessibility, provides a level of investor protection that is absent in most DeFi protocols.",
        "risks": "While U.S. Treasuries themselves carry minimal credit risk, the tokenized versions introduce additional risk layers. Smart contract risk, custodian risk, and oracle risk (for on-chain price feeds) must all be considered. Redemption mechanisms may have delays, and the token's secondary market price could temporarily deviate from the underlying NAV. Interest rate risk also applies — if rates fall, the yield on newly purchased treasuries within the fund will decrease, though this also means the market value of existing holdings increases."
    },
    "Real Estate": {
        "market_context": "Global real estate is estimated to be worth over $326 trillion, making it the world's largest store of value. Despite its enormous size, real estate has historically been one of the most illiquid asset classes, requiring significant capital outlays, lengthy due diligence periods, and complex legal structures to transact. Tokenization has the potential to fundamentally transform real estate investment by converting physical properties into divisible, tradable digital tokens on a blockchain.",
        "investor_impact": "Tokenized real estate democratizes access to property investment. Instead of needing hundreds of thousands of dollars for a down payment, investors can gain exposure to commercial office buildings, multifamily residential complexes, or industrial warehouses with investments as small as $100. This fractional ownership model enables portfolio diversification across geographies, property types, and risk profiles that was previously available only to institutional investors or ultra-high-net-worth individuals. Rental income distributions can be automated through smart contracts, paid directly to token holders in stablecoins.",
        "regulatory": "Real estate tokenization must comply with both securities regulations and property law in each jurisdiction. In the U.S., tokenized real estate offerings are typically structured as Regulation D 506(c) exemptions (for accredited investors) or Regulation A+ offerings (for broader retail access). The property itself is usually held by a Special Purpose Vehicle (SPV), and the tokens represent equity interests in that SPV rather than direct property deeds. Title insurance, property management agreements, and operating agreements must all be properly structured.",
        "risks": "Tokenized real estate carries all the traditional risks of property investment — market downturns, vacancy rates, maintenance costs, and local economic conditions — plus the additional technology risks of blockchain-based ownership. Liquidity on secondary markets for real estate tokens is still limited compared to public REITs. Valuation methodologies for tokenized properties may differ from traditional appraisals. Legal precedent for blockchain-based property ownership is still being established in most jurisdictions, creating regulatory uncertainty."
    },
    "Alternative Assets": {
        "market_context": "Alternative assets encompass a diverse range of investments outside traditional stocks, bonds, and cash — including fine art, collectibles, commodities, intellectual property, and natural resources. The global alternative assets market exceeds $13 trillion and has historically been accessible only to institutional investors and ultra-high-net-worth individuals due to high minimum investments, illiquidity, and complex ownership structures. Blockchain tokenization is breaking down these barriers by creating liquid, fractional, and transparent ownership of alternative assets.",
        "investor_impact": "For investors, tokenized alternative assets provide access to uncorrelated returns that can improve portfolio diversification. Art, wine, collectible cars, and other tangible assets have historically appreciated independently of stock market cycles, making them valuable hedges during economic downturns. Tokenization enables fractional ownership — instead of needing millions to buy a Basquiat painting, investors can purchase tokens representing a percentage of the artwork for a fraction of the cost. Smart contracts can automate revenue distribution when assets generate income or are sold at a profit.",
        "regulatory": "The regulatory framework for tokenized alternative assets varies significantly by asset type and jurisdiction. Physical assets require verified custody, insurance, and authentication processes. Digital tokens representing these assets are typically classified as securities and must comply with applicable securities laws. Specialized custodians and appraisers play critical roles in maintaining the connection between physical assets and their digital representations. Some jurisdictions have created specific regulatory sandboxes for experimenting with tokenized alternative investments.",
        "risks": "Alternative asset tokenization introduces unique risks including authenticity verification (especially for art and collectibles), storage and insurance costs for physical assets, subjective valuations that may not align with market pricing, and the potential for market manipulation in thinly traded tokens. Due diligence on the underlying assets is essential, and investors should verify that proper custody arrangements, insurance policies, and legal structures are in place before investing."
    },
    "DeFi": {
        "market_context": "Decentralized Finance (DeFi) has grown from a niche experiment to a multi-hundred-billion-dollar ecosystem that is reshaping how financial services are delivered. By replacing traditional intermediaries with smart contracts, DeFi protocols enable lending, borrowing, trading, and asset management without centralized gatekeepers. The integration of real-world assets (RWAs) into DeFi represents the next frontier, bringing trillions of dollars of traditional finance value onto programmable blockchain infrastructure.",
        "investor_impact": "The composability of DeFi — the ability to seamlessly combine different protocols like building blocks — creates powerful financial instruments that have no traditional equivalent. Tokenized RWAs can be used as collateral in lending protocols, enabling investors to borrow against their real-world holdings without selling them. Automated market makers (AMMs) can provide liquidity for tokenized assets 24/7, and yield aggregators can optimize returns across multiple protocols simultaneously. This programmable finance stack represents a paradigm shift in how capital is allocated and managed.",
        "regulatory": "The intersection of DeFi and regulated securities creates complex compliance challenges. Protocols that facilitate trading of tokenized securities must consider whether they qualify as exchanges or broker-dealers under existing regulations. KYC/AML requirements for securities transactions must be reconciled with the pseudonymous nature of DeFi wallets. Solutions like permissioned DeFi pools (where only verified wallets can participate) and on-chain identity verification are emerging to bridge this gap between regulatory compliance and decentralized architecture.",
        "risks": "DeFi protocols introduce technology risks including smart contract vulnerabilities, oracle manipulation, governance attacks, and protocol insolvency. The composability that makes DeFi powerful also creates systemic risk — a failure in one protocol can cascade through interconnected systems. Impermanent loss in liquidity pools, flash loan attacks, and rug pulls remain ongoing concerns. Investors should understand that DeFi insurance products, while available, are still nascent and may not fully cover losses."
    },
    "Regulation": {
        "market_context": "The regulatory landscape for tokenized assets is one of the most dynamic and consequential areas of financial regulation today. Governments worldwide are racing to develop frameworks that balance innovation with investor protection. The United States, European Union, Singapore, Switzerland, and the UAE have emerged as key jurisdictions shaping the rules for digital securities. Each takes a different approach, creating a complex patchwork of regulations that issuers and investors must navigate carefully.",
        "investor_impact": "Regulatory clarity directly impacts investor confidence and market participation. Clear rules attract institutional capital, improve market liquidity, and reduce legal risks for all participants. Investors benefit from regulatory frameworks that require disclosure, custody standards, and fair trading practices. However, overly restrictive regulations can stifle innovation and push activity to less regulated jurisdictions. Understanding the regulatory status of tokenized assets in your jurisdiction is essential before making any investment decisions.",
        "regulatory": "Key regulatory developments include the SEC's enforcement actions and guidance on digital securities, the EU's Markets in Crypto-Assets (MiCA) regulation (effective 2024-2025), Singapore's Payment Services Act and Securities and Futures Act modifications, Switzerland's DLT Act enabling tokenized securities, and the UAE's Virtual Assets Regulatory Authority (VARA) framework. Each jurisdiction defines different categories of digital assets and applies varying levels of regulatory requirements based on classification.",
        "risks": "Regulatory risk is perhaps the single largest risk factor for tokenized assets. Changes in regulation can render existing tokens non-compliant, restrict trading, or require costly restructuring. Cross-border regulatory conflicts can fragment markets and create legal uncertainty for international investors. The potential for retroactive enforcement actions — where regulators apply new interpretations to existing tokens — adds another layer of risk. Investors should monitor regulatory developments closely and diversify across jurisdictions where possible."
    },
    "Mortgages": {
        "market_context": "The U.S. mortgage market alone exceeds $12 trillion in outstanding loans, making it one of the largest debt markets in the world. Mortgage-backed securities (MBS) have been a cornerstone of fixed-income investing since the 1970s, but the traditional MBS market is plagued by opacity, complex tranching structures, and settlement inefficiencies. Tokenization offers the potential to bring transparency, programmability, and real-time tracking to this massive market.",
        "investor_impact": "Tokenized mortgages and mortgage-backed instruments allow investors to gain direct exposure to real estate-backed debt with greater transparency than traditional MBS. Smart contracts can automate coupon payments, principal repayments, and even default processing. Investors can track the performance of underlying mortgage pools in real-time through on-chain data, rather than relying on monthly reports from servicers. Fractional ownership of mortgage pools enables smaller investors to access this traditionally institutional asset class.",
        "regulatory": "Mortgage tokenization must comply with both securities regulations (since mortgage-backed tokens are securities) and consumer lending regulations (which govern the underlying mortgage origination). In the U.S., this involves compliance with the Securities Act, the Real Estate Settlement Procedures Act (RESPA), the Truth in Lending Act (TILA), and state-specific mortgage licensing requirements. Issuers must work with regulated mortgage originators and servicers to ensure full compliance across the lending lifecycle.",
        "risks": "Tokenized mortgages carry prepayment risk (borrowers may refinance when rates drop), default risk (borrowers may stop making payments), and interest rate risk (rising rates reduce the present value of fixed-rate mortgage payments). The complexity of mortgage underwriting, servicing, and foreclosure processes adds operational risk to the tokenization layer. Investors should carefully evaluate the credit quality of underlying mortgage pools and the track record of the servicer managing them."
    },
    "Private Equity": {
        "market_context": "The global private equity market manages over $8 trillion in assets, representing some of the highest-performing investments available. However, traditional private equity is characterized by extremely long lock-up periods (often 7-10 years), high minimum investments (typically $250,000 or more), and limited transparency. Tokenization has the potential to democratize private equity by reducing minimums, enabling secondary market liquidity, and providing real-time portfolio visibility through blockchain transparency.",
        "investor_impact": "For investors, tokenized private equity offers the prospect of accessing venture capital, growth equity, and buyout fund returns without the traditional barriers to entry. Fractional ownership through tokens can reduce minimum investments to as low as $1,000, making this asset class accessible to a much broader investor base. Perhaps most importantly, tokenization can create liquid secondary markets for PE fund interests — allowing investors to sell their positions before the fund's natural exit, solving one of the biggest pain points in traditional private equity.",
        "regulatory": "Tokenized private equity typically operates under Regulation D 506(c) exemptions in the United States, limiting participation to accredited investors. The JOBS Act and subsequent regulatory developments have expanded the definition of accredited investors and created new pathways for retail participation through Regulation A+. Fund managers must maintain compliance with the Investment Company Act, the Investment Advisers Act, and applicable state securities laws. Anti-money laundering (AML) and know-your-customer (KYC) requirements apply to all investors.",
        "risks": "Private equity investments are inherently high-risk, with the potential for total loss of capital. Tokenization does not eliminate the underlying business risk of the portfolio companies — it merely changes the ownership and trading infrastructure. Investors should be aware that secondary market liquidity for PE tokens may be limited, especially during market stress. Valuations of private companies are inherently subjective and may not reflect true market value until a liquidity event occurs."
    },
    "ESG": {
        "market_context": "Environmental, Social, and Governance (ESG) investing has grown into a $35+ trillion market globally, as investors increasingly seek to align their portfolios with sustainability goals. Tokenization brings transparency and traceability to ESG investments, enabling verifiable tracking of environmental impact, social outcomes, and governance practices through immutable blockchain records. This is particularly valuable for carbon credits, renewable energy certificates, and impact-linked financial instruments.",
        "investor_impact": "For ESG-focused investors, tokenization solves critical problems of verification and greenwashing. Every tokenized carbon credit, renewable energy certificate, or sustainability-linked bond can have its provenance, retirement, and impact tracked on a public blockchain, making it virtually impossible to double-count or misrepresent environmental benefits. Smart contracts can automatically enforce ESG covenants, trigger step-up coupons when sustainability targets are missed, and provide real-time impact reporting to investors. This transparency empowers investors to make truly informed decisions about the sustainability of their portfolios.",
        "regulatory": "ESG tokenization intersects with both securities regulation and environmental regulation. Carbon credit markets are governed by bodies like the Verified Carbon Standard (Verra) and Gold Standard, while renewable energy certificates follow jurisdiction-specific tracking systems. Tokenized ESG financial products must comply with applicable securities laws and, increasingly, with ESG-specific disclosure requirements like the EU's Sustainable Finance Disclosure Regulation (SFDR) and the SEC's proposed climate risk disclosure rules.",
        "risks": "ESG tokenization risks include the quality and additionality of underlying environmental assets, the potential for smart contract errors in impact verification, and the evolving nature of ESG standards and taxonomies. Carbon credit prices are volatile and subject to policy changes. The market for tokenized ESG assets is still nascent, with limited liquidity and standardization. Investors should conduct thorough due diligence on the underlying environmental claims and verify that independent third-party audits support the stated impact."
    },
    "Technology": {
        "market_context": "The technology infrastructure underlying tokenized assets represents one of the most rapidly evolving areas of financial technology. From Layer 1 and Layer 2 blockchain networks to decentralized oracle systems, zero-knowledge proofs, and cross-chain bridges, the technology stack for tokenization is becoming increasingly sophisticated. Understanding these technical foundations is essential for evaluating the security, scalability, and interoperability of any tokenized asset platform.",
        "investor_impact": "Technology choices directly impact the investor experience with tokenized assets. The blockchain network determines transaction speed and cost — Ethereum offers the broadest ecosystem but higher fees, while networks like Polygon, Avalanche, and Solana offer faster, cheaper transactions. Oracle networks like Chainlink provide the critical price feeds and data verification that smart contracts rely on. Cross-chain bridges enable tokens to move between different blockchains, expanding liquidity and accessibility. Investors should understand these technical tradeoffs when evaluating tokenized investment opportunities.",
        "regulatory": "Technology-focused regulation for tokenized assets includes data privacy requirements (GDPR, CCPA), cybersecurity standards, and technology-specific compliance frameworks. Regulators are increasingly scrutinizing the technology infrastructure of tokenization platforms, including smart contract auditing, key management practices, and disaster recovery procedures. Some jurisdictions require specific technology standards for regulated digital securities platforms, including minimum security certifications and interoperability requirements.",
        "risks": "Technology risks in tokenization include smart contract vulnerabilities (which have led to billions in losses across DeFi), private key management failures, oracle manipulation, and cross-chain bridge exploits. Network congestion can make transactions prohibitively expensive during high-demand periods. The rapid pace of technological change means that today's cutting-edge infrastructure may become obsolete, requiring costly migrations. Quantum computing developments could potentially threaten current cryptographic security assumptions in the long term."
    }
}

# Generic sections for categories not explicitly covered
DEFAULT_SECTIONS = {
    "market_context": "The tokenization of real-world assets (RWAs) represents one of the most significant innovations in modern finance. By converting ownership rights to physical or financial assets into digital tokens on a blockchain, tokenization enables fractional ownership, 24/7 trading, programmable compliance, and near-instantaneous settlement. Industry analysts project the tokenized asset market to exceed $10 trillion by 2030, fundamentally reshaping how assets are issued, traded, and managed across the global financial system.",
    "investor_impact": "For investors, tokenized assets offer several key advantages over traditional investment structures. Fractional ownership reduces minimum investment requirements from thousands or millions of dollars to as little as $1, enabling unprecedented portfolio diversification. Blockchain-based settlement eliminates the multi-day clearing process inherent in traditional securities, freeing up capital more efficiently. Smart contracts automate dividend distributions, corporate actions, and compliance checks, reducing costs and human error. Perhaps most importantly, tokenization creates new liquid markets for traditionally illiquid assets.",
    "regulatory": "The regulatory framework for tokenized assets is rapidly evolving across major jurisdictions. In the United States, the SEC applies existing securities laws to digital assets through frameworks like Regulation A+, Regulation D, and Regulation S. The European Union's Markets in Crypto-Assets (MiCA) regulation provides a comprehensive framework for crypto-asset service providers. Singapore's Monetary Authority, Switzerland's FINMA, and the UAE's VARA have all established progressive regulatory sandboxes and licensing regimes. Compliance with applicable securities laws, AML/KYC requirements, and investor protection rules is essential for any tokenized asset offering.",
    "risks": "Investing in tokenized assets carries inherent risks that investors should carefully evaluate. Smart contract vulnerabilities could compromise the security of tokens. Regulatory changes may impact the legality or tradability of certain tokenized instruments. Secondary market liquidity for many tokenized assets remains limited compared to traditional markets, potentially making it difficult to exit positions quickly. Custody solutions for digital securities are still maturing, and investors should verify that proper institutional-grade custody arrangements are in place. As with any investment, past performance is not indicative of future results."
}

def expand_article(article):
    """Expand an article's content to 800+ words if it's currently under that threshold."""
    content = article.get('content', '')
    current_wc = wc(content)
    
    if current_wc >= 750:
        return content  # Already long enough
    
    title = article.get('title', '')
    category = article.get('category', 'Technology')
    excerpt = article.get('excerpt', '')
    key_takeaways = article.get('key_takeaways', [])
    
    sections = CATEGORY_SECTIONS.get(category, DEFAULT_SECTIONS)
    
    # Build expansion blocks
    expansion = ""
    
    # 1. Market Context section (if article doesn't already cover it deeply)
    expansion += f"""
        <h2>Market Context and Industry Background</h2>
        <p>{sections['market_context']}</p>
        <p>Within this broader landscape, {title.lower()} represents a particularly compelling development. {excerpt} This intersection of traditional finance and blockchain technology is creating new opportunities for investors, institutions, and asset managers who are willing to explore the frontier of digital asset ownership.</p>
"""
    
    # 2. Investor Impact
    expansion += f"""
        <h2>What This Means for Investors</h2>
        <p>{sections['investor_impact']}</p>
"""
    
    # Add key takeaways as expanded prose if they exist
    if key_takeaways:
        expansion += "        <p>Understanding the practical implications is essential for any investor considering this space. "
        for i, tk in enumerate(key_takeaways):
            if i == 0:
                expansion += f"Most importantly, {tk.lower()} "
            elif i == len(key_takeaways) - 1:
                expansion += f"Finally, {tk.lower()} "
            else:
                expansion += f"Additionally, {tk.lower()} "
        expansion += "These factors collectively shape the risk-return profile and strategic value of this tokenized asset class.</p>\n"
    
    # 3. Regulatory Landscape
    expansion += f"""
        <h2>Regulatory Landscape and Compliance</h2>
        <p>{sections['regulatory']}</p>
"""
    
    # 4. Risks and Considerations
    expansion += f"""
        <h2>Risks and Considerations</h2>
        <p>{sections['risks']}</p>
        <p>Investors should conduct thorough due diligence before allocating capital to any tokenized asset. This includes evaluating the issuer's track record, understanding the legal structure of the offering, reviewing smart contract audit reports, and assessing the depth and reliability of secondary market liquidity. Consulting with a qualified financial advisor who understands both traditional securities and digital assets is strongly recommended.</p>
"""
    
    # Insert expansion before the last closing content or at the end
    # Find the last </p> or </h2> and insert before it, or just append
    if '</p>' in content:
        # Insert after existing content
        expanded = content.rstrip() + "\n" + expansion
    else:
        expanded = content + expansion
    
    return expanded


def main():
    filepath = os.path.join(DATA, 'articles.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    expanded_count = 0
    before_stats = []
    after_stats = []
    
    for article in articles:
        before_wc = wc(article.get('content', ''))
        before_stats.append(before_wc)
        
        article['content'] = expand_article(article)
        
        after_wc = wc(article.get('content', ''))
        after_stats.append(after_wc)
        
        if after_wc > before_wc:
            expanded_count += 1
            print(f"  Expanded: {article['slug']} ({before_wc}w -> {after_wc}w)")
    
    # Save
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"  EXPANSION COMPLETE")
    print(f"{'='*60}")
    print(f"  Articles expanded: {expanded_count}/{len(articles)}")
    print(f"  Avg words BEFORE: {sum(before_stats)/len(before_stats):.0f}")
    print(f"  Avg words AFTER:  {sum(after_stats)/len(after_stats):.0f}")
    
    under_600 = sum(1 for w in after_stats if w < 600)
    under_800 = sum(1 for w in after_stats if w < 800)
    over_800 = sum(1 for w in after_stats if w >= 800)
    print(f"  Under 600w: {under_600}")
    print(f"  600-799w:   {under_800 - under_600}")
    print(f"  800w+:      {over_800}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
