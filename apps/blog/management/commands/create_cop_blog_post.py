from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.blog.models import Post, Category, Tag
from django.core.files.base import ContentFile
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create the COP climate blog post'

    def handle(self, *args, **options):
        self.stdout.write("Creating COP climate blog post...")

        # Get or create admin user
        try:
            author = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found. Please run setup_demo first.'))
            return

        # Get or create category
        category, created = Category.objects.get_or_create(
            name='Climate & Sustainability',
            defaults={'description': 'Articles about climate change and sustainable energy solutions'}
        )
        if created:
            self.stdout.write(f'Created category: {category.name}')

        # Get or create tags
        tags_data = ['COP', 'Climate Change', 'Kenya', 'Developing Countries', 'Renewable Energy']
        tags = []
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
            if created:
                self.stdout.write(f'Created tag: {tag_name}')

        # Article content (HTML formatted for CKEditor)
        content = """
<h2>The Global Climate Conversation: COP Conferences and Their Impact on Developing Nations</h2>

<p>As COP29 concluded in November 2024, the world watched another chapter in the ongoing climate negotiations. For developing countries like Kenya, these Conference of the Parties meetings represent both hope and frustration - promises of funding and technology transfer alongside the reality of insufficient action.</p>

<h3>A Brief History of Climate Diplomacy</h3>

<p>The COP process began with the 1992 Rio Earth Summit and the creation of the UNFCCC. Since then, landmark agreements like the Kyoto Protocol (1997) and Paris Agreement (2015) have set global temperature goals and emission reduction targets. COP26 in Glasgow marked a pivotal moment with renewed commitments, while COP27 in Egypt established the Loss and Damage Fund for vulnerable nations.</p>

<h3>Positive Impacts: Progress Made</h3>

<h4>1. Financial Mechanisms</h4>
<p>The Green Climate Fund (GCF) and Loss and Damage Fund provide crucial financing for climate projects. Kenya has successfully accessed GCF funding for renewable energy initiatives, demonstrating how these mechanisms can drive real change.</p>

<h4>2. Technology Transfer and Capacity Building</h4>
<p>COP agreements promote sharing of clean energy technologies. This has helped Kenya expand its geothermal and solar sectors, positioning the country as a regional leader in renewable energy adoption.</p>

<h4>3. Policy Frameworks</h4>
<p>The Paris Agreement's Nationally Determined Contributions (NDCs) framework encourages countries to develop climate strategies. Kenya's ambitious renewable energy targets reflect this global push toward sustainable development.</p>

<h3>Challenges: The Implementation Gap</h3>

<h4>1. Insufficient Funding</h4>
<p>Despite pledges of $100 billion annually for climate finance, developed nations have fallen short. This funding gap hinders adaptation and mitigation efforts in vulnerable countries.</p>

<h4>2. Adaptation vs. Mitigation Priorities</h4>
<p>While mitigation focuses on emission reductions, developing countries like Kenya face immediate adaptation needs - droughts, floods, and food security challenges that threaten livelihoods.</p>

<h4>3. Economic Development Pressures</h4>
<p>Many developing nations prioritize economic growth and poverty reduction, sometimes at odds with aggressive emission reduction timelines.</p>

<h3>Kenya's Experience: A Case Study</h3>

<p>Kenya exemplifies both progress and challenges in the COP context:</p>

<ul>
<li><strong>Renewable Energy Leadership:</strong> Kenya aims for 100% renewable energy by 2030, with projects like the 310MW Lake Turkana Wind Power plant.</li>
<li><strong>Vulnerability to Climate Impacts:</strong> Agriculture, which employs 70% of the population, faces increasing droughts and floods.</li>
<li><strong>African Diplomacy:</strong> Kenya has been a vocal advocate for developing country interests in climate negotiations.</li>
</ul>

<h3>The Path Forward: Building Equity in Climate Action</h3>

<p>To bridge the gap between COP promises and reality, several steps are needed:</p>

<ol>
<li><strong>Honoring Financial Commitments:</strong> Developed nations must meet the $100 billion annual climate finance pledge.</li>
<li><strong>Technology Access:</strong> Remove barriers to clean technology transfer through intellectual property reforms.</li>
<li><strong>Loss and Damage Support:</strong> Strengthen the Loss and Damage Fund to help countries cope with unavoidable climate impacts.</li>
<li><strong>Just Transition:</strong> Ensure climate action supports rather than hinders economic development.</li>
</ol>

<h3>Conclusion: From Promises to Action</h3>

<p>COP conferences have catalyzed important global climate action, but the outcomes remain uneven. For developing countries like Kenya, the true measure of success lies not in ambitious pledges, but in tangible support that enables sustainable development while addressing climate vulnerability.</p>

<p>As we look ahead to COP30, the international community must prioritize equity and implementation. The climate crisis doesn't respect borders, and neither should our solutions.</p>

<p><em>At Olivian Solar, we believe renewable energy represents both a solution to climate change and an opportunity for sustainable development in Kenya and across Africa. Contact us to learn how solar power can contribute to your climate goals.</em></p>
        """

        excerpt = "COP climate conferences have brought both progress and disappointment for developing nations like Kenya. This article examines the real impact of these global agreements on vulnerable countries."

        # Create the post
        post, created = Post.objects.get_or_create(
            title='COP Climate Agreements: Promises vs Reality for Developing Nations',
            defaults={
                'slug': 'cop-climate-agreements-developing-nations',
                'author': author,
                'category': category,
                'content': content.strip(),
                'excerpt': excerpt,
                'meta_title': 'COP Climate Agreements: Impact on Developing Countries Like Kenya',
                'meta_description': 'Exploring how COP climate conferences have affected developing nations, with a focus on Kenya\'s experience in renewable energy and climate adaptation.',
                'meta_keywords': 'COP, climate change, Kenya, developing countries, renewable energy, climate finance, COP29',
                'status': 'published',
                'is_featured': True,
            }
        )

        if created:
            # Add tags
            post.tags.set(tags)
            # Note: featured_image would need to be added separately
            self.stdout.write(self.style.SUCCESS(f'Successfully created blog post: {post.title}'))
            self.stdout.write(f'Slug: {post.slug}')
        else:
            self.stdout.write(self.style.WARNING(f'Blog post already exists: {post.title}'))
