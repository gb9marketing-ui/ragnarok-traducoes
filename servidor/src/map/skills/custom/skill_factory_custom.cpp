// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder

#include "skill_factory_custom.hpp"

#include <unordered_map>
#include <array>

#include "../../clif.hpp"
#include "../../mob.hpp"
#include "../../status.hpp"
#include "../../unit.hpp"
#include "../../npc.hpp"
#include "../../pc.hpp"
#include "../../script.hpp"
#include "../../log.hpp"

// NNGO: invocacoes (clones do AM_CANNIBALIZE) - cada jutsu invoca o monstro da tabela do NNGO
class SkillNngoSummon : public SkillImpl {
public:
	explicit SkillNngoSummon( e_skill skill_id ) : SkillImpl( skill_id ) {}

	void castendPos2( block_list* src, int32 x, int32 y, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		static const std::unordered_map<uint16, std::array<int32, 5>> summons = {
		{ AM_CANNIBALIZE2, { 1790, 1790, 1790, 1790, 1790 } },
		{ AM_CANNIBALIZE3, { 1789, 1789, 1789, 1789, 1789 } },
		{ AM_CANNIBALIZE4, { 1788, 1788, 1788, 1788, 1788 } },
		{ AM_CANNIBALIZE5, { 1788, 1788, 1788, 1788, 1788 } },
		{ AM_CANNIBALIZE6, { 1781, 1781, 1781, 1781, 1781 } },
		{ AM_CANNIBALIZE7, { 1772, 1772, 1772, 1772, 1772 } },
		{ AM_CANNIBALIZE8, { 1784, 1784, 1784, 1784, 1784 } },
		{ AM_CANNIBALIZE9, { 1916, 1916, 1916, 1916, 1916 } },
		{ AM_CANNIBALIZE10, { 1782, 1782, 1782, 1782, 1782 } },
		{ AM_CANNIBALIZE11, { 1787, 1787, 1787, 1787, 1787 } },
		{ AM_CANNIBALIZE12, { 1011, 1011, 1011, 1011, 1011 } },
		{ AM_CANNIBALIZE13, { 1657, 1657, 1657, 1657, 1657 } },
		{ AM_CANNIBALIZE14, { 1993, 1993, 1993, 1993, 1993 } },
		{ AM_CANNIBALIZE15, { 1994, 1994, 1994, 1994, 1994 } },
		{ AM_CANNIBALIZE16, { 1658, 1658, 1658, 1658, 1658 } },
		{ AM_CANNIBALIZE17, { 1033, 1033, 1033, 1033, 1033 } },
		{ AM_CANNIBALIZE18, { 1589, 1579, 1575, 1555, 1590 } },
		{ AM_CANNIBALIZE19, { 1324, 1324, 1324, 1324, 1324 } },
		{ AM_CANNIBALIZE20, { 1325, 1325, 1325, 1325, 1325 } },
		{ AM_CANNIBALIZE21, { 1326, 1326, 1326, 1326, 1326 } },
		{ AM_CANNIBALIZE22, { 1327, 1327, 1327, 1327, 1327 } },
		{ AM_CANNIBALIZE23, { 1328, 1328, 1328, 1328, 1328 } },
		{ AM_CANNIBALIZE24, { 1329, 1329, 1329, 1329, 1329 } },
		{ AM_CANNIBALIZE25, { 1447, 1447, 1447, 1447, 1447 } },
		{ AM_CANNIBALIZE26, { 1448, 1448, 1448, 1448, 1448 } },
		{ AM_CANNIBALIZE27, { 1449, 1449, 1449, 1449, 1449 } },
		{ AM_CANNIBALIZE28, { 1500, 1500, 1500, 1500, 1500 } },
		{ AM_CANNIBALIZE29, { 1503, 1503, 1503, 1503, 1503 } },
		{ AM_CANNIBALIZE30, { 1504, 1504, 1504, 1504, 1504 } },
		{ AM_CANNIBALIZE31, { 1505, 1505, 1505, 1505, 1505 } },
		{ AM_CANNIBALIZE32, { 1506, 1506, 1506, 1506, 1506 } },
		{ AM_CANNIBALIZE33, { 1507, 1507, 1507, 1507, 1507 } },
		{ AM_CANNIBALIZE34, { 1508, 1508, 1508, 1508, 1508 } },
		{ AM_CANNIBALIZE35, { 1509, 1509, 1509, 1509, 1509 } },
		{ AM_CANNIBALIZE36, { 1521, 1521, 1521, 1521, 1521 } },
		{ AM_CANNIBALIZE37, { 1518, 1518, 1518, 1518, 1518 } },
		{ AM_CANNIBALIZE38, { 1519, 1519, 1519, 1519, 1519 } },
		{ AM_CANNIBALIZE39, { 1520, 1520, 1520, 1520, 1520 } },
		{ AM_CANNIBALIZE40, { 1589, 1579, 1575, 1555, 1590 } }
		};
		auto it = summons.find( getSkillId() );

		if( it == summons.end() )
			return;

		int32 class_ = it->second[std::clamp<int32>( skill_lv, 1, 5 ) - 1];
		mob_data* md = mob_once_spawn_sub( src, src->m, x, y, status_get_name( *src ), class_, "", SZ_SMALL, AI_FLORA );

		if( md != nullptr ){
			md->master_id = src->id;
			md->special_state.ai = AI_FLORA;
			if( md->deletetimer != INVALID_TIMER )
				delete_timer( md->deletetimer, mob_timer_delete );
			md->deletetimer = add_timer( gettick() + skill_get_time( getSkillId(), skill_lv ), mob_timer_delete, md->id, 0 );
			mob_spawn( md );
		}
	}
};

// NNGO: genjutsus (clones do BA_PANGVOICE) - confusao com 50% de chance, como no NNGO
class SkillNngoPangVoice : public SkillImpl {
public:
	explicit SkillNngoPangVoice( e_skill skill_id ) : SkillImpl( skill_id ) {}

	void castendNoDamageId( block_list* src, block_list* target, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		clif_skill_nodamage( src, *target, getSkillId(), skill_lv, sc_start( src, target, SC_CONFUSION, 50, 7, skill_get_time( getSkillId(), skill_lv ) ) );
	}
};

// NNGO: DOTASWAP - troca de posicao com o alvo
class SkillNngoSwap : public SkillImpl {
public:
	SkillNngoSwap() : SkillImpl( DOTASWAP ) {}

	void castendNoDamageId( block_list* src, block_list* target, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		if( target->type == BL_MOB ){
			static const int32 blocked[] = { 1694,1089,1099,1331,1332,1333,1334,1576,1069,1045,1001,1330,1335,1336,1337,1338,1339,1340,1341 };
			const mob_data* md = BL_CAST( BL_MOB, target );

			for( int32 id : blocked ){
				if( md->mob_id == id )
					return;
			}
		}

		int16 x = src->x, y = src->y;

		unit_movepos( src, target->x, target->y, 1, true );
		clif_slide( *src, target->x, target->y );
		unit_movepos( target, x, y, 1, true );
		clif_slide( *target, x, y );
		clif_specialeffect( target, 34, AREA );
		clif_specialeffect( src, 34, AREA );
		clif_skill_nodamage( src, *target, getSkillId(), skill_lv );
	}
};

// NNGO: GODD_SPLASPD / GODD_SPLSWALK - deixa o alvo lento (ataque / movimento)
class SkillNngoSlow : public SkillImpl {
	sc_type type; int32 effect;
public:
	SkillNngoSlow( e_skill id, sc_type t, int32 e ) : SkillImpl( id ), type( t ), effect( e ) {}

	void castendNoDamageId( block_list* src, block_list* target, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		clif_specialeffect( target, effect, AREA );
		clif_skill_nodamage( src, *target, getSkillId(), skill_lv, sc_start( src, target, type, 100, skill_lv, skill_get_time( getSkillId(), skill_lv ) ) );
	}
};

// NNGO: GODD_PULLEN - puxa o alvo para perto do usuario
class SkillNngoPull : public SkillImpl {
public:
	SkillNngoPull() : SkillImpl( GODD_PULLEN ) {}

	void castendNoDamageId( block_list* src, block_list* target, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		if( target->type == BL_MOB ){
			static const int32 blocked[] = { 1694,1089,1099,1330,1331,1332,1333,1334,1335,1336,1337,1338,1339,1340,1341 };
			const mob_data* md = BL_CAST( BL_MOB, target );

			for( int32 id : blocked ){
				if( md->mob_id == id )
					return;
			}
		}

		clif_specialeffect( target, 34, AREA );
		unit_movepos( target, src->x, src->y, 1, true );
		clif_slide( *target, src->x, src->y );
		clif_specialeffect( target, 34, AREA );
		clif_skill_nodamage( src, *target, getSkillId(), skill_lv, false );
	}
};

// NNGO: GODD_STEALSOMETHING ("Roubar chakra") - com o alvo abaixo de 1/3 do HP, 10% de chance de roubar cada item da lista
class SkillNngoSteal : public SkillImpl {
public:
	SkillNngoSteal() : SkillImpl( GODD_STEALSOMETHING ) {}

	void castendNoDamageId( block_list* src, block_list* target, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		map_session_data* sd = BL_CAST( BL_PC, src );
		map_session_data* dstsd = BL_CAST( BL_PC, target );

		if( sd == nullptr || dstsd == nullptr || dstsd->battle_status.hp == 0 )
			return;
		if( dstsd->battle_status.max_hp / dstsd->battle_status.hp < 3 )
			return;

		static const t_itemid items[] = { 616, 4409, 4253, 4254 };

		for( t_itemid nameid : items ){
			int16 idx = pc_search_inventory( dstsd, nameid );

			if( idx < 0 || rnd() % 100 >= 10 )
				continue;

			item tmp = dstsd->inventory.u.items_inventory[idx];

			if( pc_delitem( dstsd, idx, 1, 0, 0, LOG_TYPE_STEAL ) == 0 )
				pc_additem( sd, &tmp, 1, LOG_TYPE_STEAL );
		}
	}
};

// NNGO: NARUTO_CAPTUREBIJUU - com a Bijuu abaixo de 20% do HP, chama o evento de captura
class SkillNngoCaptureBijuu : public SkillImpl {
public:
	SkillNngoCaptureBijuu() : SkillImpl( NARUTO_CAPTUREBIJUU ) {}

	void castendNoDamageId( block_list* src, block_list* target, uint16 skill_lv, t_tick tick, int32& flag ) const override {
		map_session_data* sd = BL_CAST( BL_PC, src );
		mob_data* md = BL_CAST( BL_MOB, target );

		if( sd == nullptr )
			return;
		if( md == nullptr ){
			clif_displaymessage( sd->fd, "S\xf3 pode ser usado em Bijuu." );
			return;
		}
		if( md->status.hp == 0 || md->status.max_hp / md->status.hp < 5 ){
			clif_displaymessage( sd->fd, "O HP dela ainda n\xe3o est\xe1 abaixo de 20%." );
			return;
		}

		static const int32 bijuus[] = { 1086, 1983, 1738, 1985, 1981, 1982, 1737, 1984, 1986 };

		for( int32 id : bijuus ){
			if( id == md->mob_id ){
				pc_setreg( sd, add_str( "@bijuu_class" ), id );
				pc_setreg( sd, add_str( "@bijuu_gid" ), md->id );
				npc_event( sd, "NarutoSKillMainEvent::OnCaptureBijuu", 0 );
				break;
			}
		}

		clif_skill_nodamage( src, *target, getSkillId(), skill_lv );
	}
};

std::unique_ptr<const SkillImpl> SkillFactoryCustom::create(const e_skill skill_id) const {
	switch( skill_id ){
		case AM_CANNIBALIZE2:
		case AM_CANNIBALIZE3:
		case AM_CANNIBALIZE4:
		case AM_CANNIBALIZE5:
		case AM_CANNIBALIZE6:
		case AM_CANNIBALIZE7:
		case AM_CANNIBALIZE8:
		case AM_CANNIBALIZE9:
		case AM_CANNIBALIZE10:
		case AM_CANNIBALIZE11:
		case AM_CANNIBALIZE12:
		case AM_CANNIBALIZE13:
		case AM_CANNIBALIZE14:
		case AM_CANNIBALIZE15:
		case AM_CANNIBALIZE16:
		case AM_CANNIBALIZE17:
		case AM_CANNIBALIZE18:
		case AM_CANNIBALIZE19:
		case AM_CANNIBALIZE20:
		case AM_CANNIBALIZE21:
		case AM_CANNIBALIZE22:
		case AM_CANNIBALIZE23:
		case AM_CANNIBALIZE24:
		case AM_CANNIBALIZE25:
		case AM_CANNIBALIZE26:
		case AM_CANNIBALIZE27:
		case AM_CANNIBALIZE28:
		case AM_CANNIBALIZE29:
		case AM_CANNIBALIZE30:
		case AM_CANNIBALIZE31:
		case AM_CANNIBALIZE32:
		case AM_CANNIBALIZE33:
		case AM_CANNIBALIZE34:
		case AM_CANNIBALIZE35:
		case AM_CANNIBALIZE36:
		case AM_CANNIBALIZE37:
		case AM_CANNIBALIZE38:
		case AM_CANNIBALIZE39:
		case AM_CANNIBALIZE40:
			return std::make_unique<SkillNngoSummon>( skill_id );
		case BA_PANGVOICE2:
		case BA_PANGVOICE3:
		case BA_PANGVOICE4:
		case BA_PANGVOICE5:
		case BA_PANGVOICE6:
		case BA_PANGVOICE7:
		case BA_PANGVOICE8:
		case BA_PANGVOICE9:
		case BA_PANGVOICE10:
		case BA_PANGVOICE11:
		case BA_PANGVOICE12:
		case BA_PANGVOICE13:
		case BA_PANGVOICE14:
		case BA_PANGVOICE15:
		case BA_PANGVOICE16:
		case BA_PANGVOICE17:
		case BA_PANGVOICE18:
		case BA_PANGVOICE19:
		case BA_PANGVOICE20:
		case BA_PANGVOICE21:
		case BA_PANGVOICE22:
		case BA_PANGVOICE23:
		case BA_PANGVOICE24:
		case BA_PANGVOICE25:
		case BA_PANGVOICE26:
		case BA_PANGVOICE27:
		case BA_PANGVOICE28:
		case BA_PANGVOICE29:
		case BA_PANGVOICE30:
		case BA_PANGVOICE31:
		case BA_PANGVOICE32:
		case BA_PANGVOICE33:
		case BA_PANGVOICE34:
		case BA_PANGVOICE35:
		case BA_PANGVOICE36:
		case BA_PANGVOICE37:
		case BA_PANGVOICE38:
		case BA_PANGVOICE39:
		case BA_PANGVOICE40:
		case BA_PANGVOICE41:
		case BA_PANGVOICE42:
		case BA_PANGVOICE43:
		case BA_PANGVOICE44:
		case BA_PANGVOICE45:
		case BA_PANGVOICE46:
		case BA_PANGVOICE47:
		case BA_PANGVOICE48:
		case BA_PANGVOICE49:
		case BA_PANGVOICE50:
		case BA_PANGVOICE50_981:
		case BA_PANGVOICEZ:
		case BA_PANGVOICEZ1:
		case BA_PANGVOICEZ2:
		case BA_PANGVOICEX:
			return std::make_unique<SkillNngoPangVoice>( skill_id );
		case DOTASWAP:
			return std::make_unique<SkillNngoSwap>();
		case GODD_SPLASPD:
			return std::make_unique<SkillNngoSlow>( GODD_SPLASPD, SC_SUPERSLOWAPSD, 413 );
		case GODD_SPLSWALK:
			return std::make_unique<SkillNngoSlow>( GODD_SPLSWALK, SC_SUPERSLOWWALK, 415 );
		case GODD_PULLEN:
			return std::make_unique<SkillNngoPull>();
		case GODD_STEALSOMETHING:
			return std::make_unique<SkillNngoSteal>();
		case NARUTO_CAPTUREBIJUU:
			return std::make_unique<SkillNngoCaptureBijuu>();
		default:
			return nullptr;
	}
}
